# all treatment of container_images aka images

from copy import deepcopy
from pathlib import Path

from flask import Blueprint, \
    redirect, \
    request, \
    render_template

from backend.database import couchdb
from frontend.misc import is_htmx


db = couchdb.get_database_object('container_images')

# tabs for container repository details
container_image_TABS = ['tags', 'readme']

# take name for blueprint from file for flawless copy&paste
blueprint = Blueprint(Path(__file__).stem, __name__)


@blueprint.route('/<container_image_hash>/tab/<tab>/filter', methods=['GET', 'POST'])
@blueprint.route('/<container_image_hash>/tab/<tab>', methods=['GET'])
@blueprint.route('/<container_image_hash>', methods=['GET'])
def container_image(container_image_hash: int = None, tab=None):
    """
    Requests regarding container details are processed here
    :param container_image_hash:
    :param tab:
    :return:
    """
    search_string = ''
    filter_string = ''

    search_result_db = db.find(selector={'hash': container_image_hash}, use_index='hash')

    pass
    # only process if there was a valid container involved
    if search_result_db and len(search_result_db) == 1:
        # tab to be shown
        tab_selected = tab
        # if there is none the first one will be chosen
        if not tab:
            template = 'container_image/index.html'
            tab_selected = container_image_TABS[0]
        elif is_htmx() and tab in container_image_TABS:
            if request.form.get('filter') or request.form.get('filter') == '':
                filter_string = request.form['filter'].strip().lower()
            # direct calls via GET will receive the start view
            if not filter_string and request.method == 'GET':
                template = 'container_image/tabs.html'
            # filtering attempts will receive a filtered list
            else:
                template = 'container_image/tab/tags_list.html'
        # get single requested repository - can only be one
        container_image = search_result_db[0]
        # search_string is for back-button
        if request.args.get('search_string'):
            search_string = request.args['search_string']
        # htmx-based request
        if tab and \
                is_htmx() and \
                tab in container_image_TABS:
            filter_string = ''
            if request.form.get('filter') or request.form.get('filter') == '':
                # to be refined
                filter_string = request.form['filter'].strip().lower()
            if filter_string and request.method == 'POST':
                filter_results = dict()
                for name, tag in container_image['tags'].items():
                    if filter_string.lower() in name.lower():
                        filter_results.update({name: tag})
                # get a copy of container_image to use filtered tags
                container_image_filtered = deepcopy(container_image)
                container_image_filtered['tags'] = filter_results
                # use filtered copy
                container_image = container_image_filtered
        return render_template(template,
                               container_image=container_image,
                               container_image_hash=container_image_hash,
                               container_image_TABS=container_image_TABS,
                               is_htmx=is_htmx(),
                               search_string=search_string,
                               filter_string=filter_string,
                               tab=tab_selected)
    return redirect('/')
