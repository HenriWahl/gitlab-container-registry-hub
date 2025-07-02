#from dataclasses import dataclass, \
#    field
from datetime import datetime, \
    timezone
from json import loads
#from json.decoder import JSONDecodeError
from time import sleep

from datasize import DataSize
from dateutil import parser as dateutil_parser, \
    relativedelta
from markdown import markdown

from backend.config import API_SUFFIX, \
                           config
from backend.connection import gitlab_session_get
from backend.database import couchdb
from backend.helpers import plural_or_not, \
    exit

def collect_projects() -> list:
    """
    collect all projects
    :return:
    """
    projects_list = list()
    # due to pagination, we have to start with some 1
    projects_page = 1
    projects_total_pages = 1

    # GitLab maximally returns 100 projects per page, so we have to loop through all pages
    while projects_page <= projects_total_pages:
        response = gitlab_session_get(f'{config.api.url}{API_SUFFIX}/projects',
                                      params={'page': projects_page,
                                              'per_page': 100})
        if response.status_code < 400:
            # header 'x-total-pages' tells into how many pages the results are split
            projects_total_pages = int(response.headers.get('x-total-pages'))
            projects_page += 1
            projects_list += loads(response.text)
        elif response.status_code == 401:
            # when token is unauthorized exit immediately
            exit(f'status_code: {response.status_code} text: {response.text}')
        else:
            print(f'status_code: {response.status_code} text: {response.text}')
            # try agin after a short nap
            sleep(20)

    for project in projects_list:
        # fix None project description
        if not project['description']:
            project['description'] = ''

    return projects_list


def collect_project_container_images(project) -> dict:
    """
    enrich container_images with details of projects
    :param container_images:
    :param projects_list:
    :return:
    """

    result = list()

    project_id = project.get('id')
    response = gitlab_session_get(f'{config.api.url}{API_SUFFIX}/projects/{project_id}/registry/repositories',
                                  params={'tags': True,
                                          'tags_count': True,
                                          'size': True})
    repositories = loads(response.text)

    if repositories:
        # collect all images of a project
        for container_image in repositories:
            container_image['project'] = project
            # fix name which basically is the same as path
            container_image['name'] = container_image['location']
            result.append(container_image)
    return result


def collect_project_container_images_tag(container_image: dict) -> dict:
    """
    get all tags of a container repository of a project
    :param container_image:
    :return:
    """
    container_image_id = container_image['id']
    project_id = container_image['project_id']
    tags = dict()
    for tag in container_image['tags']:
        tag_name = tag.get('name')
        response = gitlab_session_get(
            f'{config.api.url}{API_SUFFIX}/projects/{project_id}/registry/repositories/{container_image_id}/tags/{tag_name}',
            params={'tags': True,
                    'tags_count': True,
                    'size': True})
        tags[tag_name] = loads(response.text)
    # overwrite tags with more detailed info
    container_image['tags'] = tags
    return container_image


def collect_project_container_image_tags_humanize(container_image: dict) -> dict:
    """
    get all tags of a container repository of a project
    :param container_image:
    :return:
    """
    # 'now' is needed for age calculation of images
    NOW = datetime.now(timezone.utc)

    # empty default values may better be '' than None to avoid concat crashes
    container_image['last_update'] = ''
    container_image['last_update_tag'] = ''
    # 'tag' will be identical to 'last_update_tag' and stored for sortability in the UI
    container_image['tag'] = ''
    # get last update date
    for tag in container_image['tags'].values():
        # parse time string from Gitlab into datetime object
        print(container_image.get('location'), tag.get('created_at'), tag)
        if tag.get('created_at'):
            tag_created_at = dateutil_parser.parse(tag.get('created_at'))
            # when currently checked tag is newer than latest known it become the new last_update
            if container_image['last_update']:
                if container_image['last_update'] < tag_created_at:
                    container_image['last_update'] = tag_created_at
                    container_image['last_update_tag'] = tag['name']
                    container_image['tag'] = tag['name']
            else:
                container_image['last_update'] = tag_created_at
                container_image['last_update_tag'] = tag['name']
                container_image['tag'] = tag['name']
            # add human-readable tag image size
            tag['total_size_human_readable'] = '{:.2MiB}'.format(DataSize(tag['total_size']))
            # add human-readable tag creation date
            tag['created_at_human_readable'] = dateutil_parser.parse(tag['created_at']).strftime(
                '%Y-%m-%d %H:%M:%S')

    # get age of a container image
    # relativedelta adds all other units like 'years=0' which makes it better comparable
    age = relativedelta.relativedelta(NOW, container_image['last_update'])
    #container_images['age'] = age
    # store creation date as difference between now and age
    container_image['created'] = NOW - age
    # get a human-readable version of age to be read by humans
    container_image['age_human_readable'] = ''
    age_human_readable = 'n/a'
    if age.years > 0:
        age_human_readable = f'{plural_or_not(age.years, "year")}'
    elif age.months > 0:
        age_human_readable = f'{plural_or_not(age.months, "month")}'
    elif age.weeks > 0:
        age_human_readable = f'{plural_or_not(age.weeks, "week")}'
    elif age.days > 0:
        age_human_readable = f'{plural_or_not(age.days, "day")}'
    elif age.hours > 0:
        age_human_readable = f'{plural_or_not(age.hours, "hour")}'
    elif age.seconds > 0:
        age_human_readable = f'{plural_or_not(age.seconds, "second")}'
    age_human_readable = f'{age_human_readable}'
    container_image['age_human_readable'] = age_human_readable

    return container_image


def collect_project_container_image_tags_compare_revisions(container_image: dict) -> dict:
    """
    get revision hashes for tags which share a revision to make it clear they belong together
    """
    # store all revisions
    revisions = dict()
    # consider every tag
    for tag, properties in container_image['tags'].items():
        revision = properties.get('revision')
        # default is no background color
        properties['tag_revision_background_color'] = ''
        if revision:
            revisions.setdefault(revision, list())
            revisions[revision].append(tag)
    # change only background color for those which have more than 1 which have the same revision
    for revision in [x for x in revisions.keys() if len(revisions[x]) > 1]:
        for tag, properties in container_image['tags'].items():
            if tag in revisions[revision]:
                properties['tag_revision_background_color'] = revision[0:6]
    return container_image


def collect_project_container_image_readme(container_image: dict) -> dict:
    """
    get readme of a project and add to container images
    :param container_image:
    :return:
    """
    project = container_image['project']
    project_id = project['id']
    if project.get('readme_url'):
        readme_file = project['readme_url'].split('/')[-1]
        response = gitlab_session_get(
            f'{config.api.url}{API_SUFFIX}/projects/{project_id}/repository/files/{readme_file}/raw',
            params={'id': project_id,
                    'file_path': readme_file,
                    'ref': 'HEAD'})

        container_image['readme_md'] = response.text
        readme_html = markdown(response.text,
                               extensions=['attr_list',
                                           'def_list',
                                           'fenced_code',
                                           'md_in_html',
                                           'tables'])
        # decrease the size of headers to make the README tab more readable
        readme_html = readme_html.replace('<h5>', '<h6>').replace('</h5>', '</h6>')
        readme_html = readme_html.replace('<h4>', '<h6>').replace('</h4>', '</h6>')
        readme_html = readme_html.replace('<h3>', '<h5>').replace('</h3>', '</h5>')
        readme_html = readme_html.replace('<h2>', '<h4>').replace('</h2>', '</h4>')
        readme_html = readme_html.replace('<h1>', '<h3>').replace('</h1>', '</h3>')
        container_image['readme_html'] = readme_html

    return container_image


def collect_container_image():
    """
    recursively request information about projects, their container images and their respective tags
    :return: container_images
    """
    # dict for storage of container image info
    # will be enriched with infos about:
    # - projects
    # - tags
    # - identical revision hashes
    # - last_update
    # - age
    #container_images = dict()

    db = couchdb.get_database_object('container_images')

    # collect all projects
    projects_list = collect_projects()
    for project in [x for x in projects_list if x.get('container_registry_enabled')]:
        # details of every project are to be collected one by one, only from those which
        container_images = collect_project_container_images(project)
        if container_images:
            for container_image in container_images:
                # add tag information
                container_image = collect_project_container_images_tag(container_image)
                # add last update and human-readable size information
                container_image = collect_project_container_image_tags_humanize(container_image)
                container_image = collect_project_container_image_tags_compare_revisions(container_image)
                container_image = collect_project_container_image_readme(container_image)

                db.store(container_image['location'], container_image)


def run_collector():
    while True:
        collect_container_image()
        sleep(config.update_interval)

