from dataclasses import dataclass, \
    field
from datetime import datetime, \
    timezone
from json import loads
from threading import Thread
from time import sleep

from datasize import DataSize
from dateutil import parser as dateutil_parser, \
    relativedelta
from markdown import markdown

from backend.config import config
from backend.connection import gitlab_session
from backend.helpers import plural_or_not

# for now all requested URLs start with this suffix
API_SUFFIX = '/api/v4'

class ContainerImageCache(dict):
    """
    dict-based class to act as cache
    """
    def __init__(self):
        super().__init__()
        # actual container repositories cache
        self.container_images = dict()
        # meta information like number of containers
        self.meta = dict()
        # prefilled index to access container information by name
        self.index_by_name = dict()

    def update_cache(self, container_images):
        """
        add new container repositories and delete not anymore existing ones
        :param container_images:
        :return:
        """
        for container_image_cached in self.keys():
            # throw away cached container repository if it does not exist in new info
            if not container_image_cached in container_images.keys():
                self.pop(container_image_cached)
        self.container_images.update(container_images)
        self.create_index_by_name()


    def create_index_by_name(self):
        """
        allow to access container repositories by their name to make them searchable
        :return:
        """
        for container_image in self.container_images.values():
            self.index_by_name[container_image['path']] = container_image


class CollectorThread(Thread):
    """
    collects info from Gitlab at certain interval
    """
    def __init__(self):
        Thread.__init__(self, name='Collector')

    def run(self):
        global container_images_cache
        global update_status
        while True:
            container_images_cache.update_cache(self.collect_container_images())
            sleep(config.update_interval)

    def collect_container_images(self):
        """
        recursively request information about projects, their container images and their respective tags
        :return: container_images
        """
        # to speedup development and avoid waiting for Gitlab response dump the latter
        if config.load_data:
            import pickle
            with open('container_images_dump.pickle','rb') as pickle_file:
                container_images = pickle.load(pickle_file)
        else:
            # dict for storage of container image info
            # will be enriched with infos about:
            # - projects
            # - tags
            # - identical revision hashes
            # - last_update
            # - age
            container_images = dict()
            # counter for GUI progress bar
            update_status.number_of_current_stage = 0

            # collect all projects
            update_status.current_stage = 'collecting projects'
            update_status.number_of_current_stage += 1
            projects_list = self.collect_projects()
            # details of every project are to be collected one by one, only from those which
            update_status.current_stage = 'collecting details of projects'
            update_status.number_of_current_stage += 1
            container_images = self.collect_project_container_images(container_images, projects_list)
            # add tag information
            update_status.current_stage = 'collecting tag information'
            update_status.number_of_current_stage += 1
            container_images = self.collect_project_container_images_tags(container_images)
            # add last update and human readable size information
            update_status.current_stage = 'make information human readable'
            update_status.number_of_current_stage += 1
            container_images = self.collect_project_container_images_tags_humanize(container_images)
            update_status.current_stage = 'find identical revision hashes'
            update_status.number_of_current_stage += 1
            container_images = self.collect_project_container_images_tags_compare_revisions(container_images)
            # collect README.md per project
            update_status.current_stage = 'collect README files'
            update_status.number_of_current_stage += 1
            container_images = self.collect_project_container_images_readme(container_images)
            # ready!
            update_status.current_stage = ''
            update_status.timestamp = datetime.now()

        # to speedup development and avoid waiting for Gitlab response dump the latter
        if config.dump_data:
            import pickle
            with open('container_images_dump.pickle','wb') as pickle_file:
                pickle.dump(container_images, pickle_file)

        # make update progress bar unnecessary
        update_status.initialized = True

        return container_images

    @staticmethod
    def collect_projects() -> list:
        """
        collect all projects
        :return:
        """
        projects_list = list()
        # due to pagination we have to start with some 1
        projects_page = 1
        projects_total_pages = 1

        while projects_page <= projects_total_pages:
            response = gitlab_session.get(f'{config.api.url}{API_SUFFIX}/projects',
                                          params={'page': projects_page,
                                                  'per_page': 100})
            if response.status_code < 400:
                # header 'x-total-pages' tells into how many pages the results are split
                projects_total_pages = int(response.headers.get('x-total-pages'))
                projects_page += 1
                projects_list += loads(response.text)

        for project in projects_list:
            # fix None project description
            if not project['description']:
                project['description'] = ''

        return projects_list

    @staticmethod
    def collect_project_container_images(container_images: dict, projects_list: list) -> dict:
        """
        enrich container_images with details of projects
        :param container_images:
        :param projects_list:
        :return:
        """
        for project in [x for x in projects_list if x.get('container_registry_enabled')]:
            project_id = project.get('id')
            response = gitlab_session.get(f'{config.api.url}{API_SUFFIX}/projects/{project_id}/registry/repositories',
                                          params={'tags': True,
                                                  'tags_count': True,
                                                  'size': True})
            repository = loads(response.text)
            if repository:
                # collect all images of a project
                for container_image in repository:
                    container_image_id = container_image.get('id')
                    container_images[container_image_id] = container_image
                    container_images[container_image_id]['project'] = project
                    # fix name which basically is the same as path
                    container_images[container_image_id]['name'] = container_image['path']
        return container_images

    @staticmethod
    def collect_project_container_images_tags(container_images: dict) -> dict:
        """
        get all tags of a container repository of a project
        :param container_images:
        :return:
        """
        for container_image_id in container_images.keys():
            project_id = container_images[container_image_id]['project_id']
            tags = dict()
            for tag in container_images[container_image_id]['tags']:
                tag_name = tag.get('name')
                response = gitlab_session.get(
                    f'{config.api.url}{API_SUFFIX}/projects/{project_id}/registry/repositories/{container_image_id}/tags/{tag_name}',
                    params={'tags': True,
                            'tags_count': True,
                            'size': True})
                tags[tag_name] = loads(response.text)
            # overwrite tags with more detailed info
            container_images[container_image_id]['tags'] = tags
        return container_images

    @staticmethod
    def collect_project_container_images_tags_humanize(container_images: dict) -> dict:
        """
        get all tags of a container repository of a project
        :param container_images:
        :return:
        """
        # 'now' is needed for age calculation of images
        NOW = datetime.now(timezone.utc)

        for container_image_id in container_images.keys():
            # empty default values may better be '' than None to avoid concat crashes
            container_images[container_image_id]['last_update'] = ''
            container_images[container_image_id]['last_update_tag'] = ''
            # 'tag' will be identical to 'last_update_tag' and stored for sortability in the UI
            container_images[container_image_id]['tag'] = ''
            # get last update date
            for tag in container_images[container_image_id]['tags'].values():
                # parse time string from Gitlab into datetime object
                tag_created_at = dateutil_parser.parse(tag.get('created_at'))
                # when currently checked tag is newer than latest known it become the new last_update
                if container_images[container_image_id]['last_update']:
                    if container_images[container_image_id]['last_update'] < tag_created_at:
                        container_images[container_image_id]['last_update'] = tag_created_at
                        container_images[container_image_id]['last_update_tag'] = tag['name']
                        container_images[container_image_id]['tag'] = tag['name']
                else:
                    container_images[container_image_id]['last_update'] = tag_created_at
                    container_images[container_image_id]['last_update_tag'] = tag['name']
                    container_images[container_image_id]['tag'] = tag['name']
                # add human readable tag image size
                tag['total_size_human_readable'] = '{:.2MiB}'.format(DataSize(tag['total_size']))
                # add human readable tag creation date
                tag['created_at_human_readable'] =  dateutil_parser.parse(tag['created_at']).strftime('%Y-%m-%d %H:%M:%S')

            # get age of a container image
            # relativedelta adds all other units like 'years=0' which makes it better comparable
            age = relativedelta.relativedelta(NOW, container_images[container_image_id]['last_update'])
            container_images[container_image_id]['age'] = age
            # store creation date as diffenrence between now and age
            container_images[container_image_id]['created'] = NOW - age
            # get human readable version of age to be read by humans
            container_images[container_image_id]['age_human_readable'] = ''
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
            container_images[container_image_id]['age_human_readable'] = age_human_readable
        return container_images

    @staticmethod
    def collect_project_container_images_tags_compare_revisions(container_images: dict) -> dict:
        """
        get revision hashes for tags which share a revision to make it clear they belong together
        """
        for container_image_id in container_images.keys():
            # store all revisions
            revisions = dict()
            # consider every tag
            for tag, properties in container_images[container_image_id]['tags'].items():
                revision = properties.get('revision')
                # default is no background color
                properties['tag_revision_background_color'] = ''
                if revision:
                    revisions.setdefault(revision, list())
                    revisions[revision].append(tag)
            # change only background color for those which have more than 1 which have the same revision
            for revision in [x for x in revisions.keys() if len(revisions[x]) > 1]:
                for tag, properties in container_images[container_image_id]['tags'].items():
                    if tag in revisions[revision]:
                        properties['tag_revision_background_color'] = revision[0:6]
        return container_images

    @staticmethod
    def collect_project_container_images_readme(container_images: dict) -> dict:
        """
        get readme of a project and add to container images
        :param container_images:
        :return:
        """
        for container_image_id in container_images.keys():
            project = container_images[container_image_id]['project']
            project_id = project['id']
            if project.get('readme_url'):
                readme_file = project['readme_url'].split('/')[-1]
                response = gitlab_session.get(
                    f'{config.api.url}{API_SUFFIX}/projects/{project_id}/repository/files/{readme_file}/raw',
                    params={'id': project_id,
                            'file_path': readme_file,
                            'ref': 'HEAD'})

                container_images[container_image_id]['readme_md'] = response.text
                readme_html = markdown(response.text,
                                       extensions=['attr_list',
                                                   'def_list',
                                                   'fenced_code',
                                                   'md_in_html',
                                                   'tables'])
                # decrease size of headers to make the README tab more readable
                readme_html = readme_html.replace('<h5>', '<h6>').replace('</h5>', '</h6>')
                readme_html = readme_html.replace('<h4>', '<h6>').replace('</h4>', '</h6>')
                readme_html = readme_html.replace('<h3>', '<h5>').replace('</h3>', '</h5>')
                readme_html = readme_html.replace('<h2>', '<h4>').replace('</h2>', '</h4>')
                readme_html = readme_html.replace('<h1>', '<h3>').replace('</h1>', '</h3>')
                container_images[container_image_id]['readme_html'] = readme_html

        return container_images


@dataclass
class UpdateStatus:
    """
    store info about update
    """
    current_stage: str = ''
    number_of_stages: int = 6
    number_of_current_stage: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    initialized: bool = False


# object for documenting update collection
update_status = UpdateStatus()

# to be imported by others
container_images_cache = ContainerImageCache()