# all treatment of container_images aka images

from copy import deepcopy
from pathlib import Path

from flask import Blueprint, \
    redirect, \
    request, \
    render_template

from backend.collect import container_images_cache
from frontend.misc import is_htmx


# tabs for container repository details
container_image_TABS = ['tags', 'readme']

# take name for blueprint from file for flawless copy&paste
blueprint = Blueprint(Path(__file__).stem, __name__)


@blueprint.route('/<int:container_image_id>/tab/<tab>/filter', methods=['GET', 'POST'])
@blueprint.route('/<int:container_image_id>/tab/<tab>', methods=['GET'])
@blueprint.route('/<int:container_image_id>', methods=['GET'])
def container_image(container_image_id: int = None, tab=None):
    """
    Requests regarding container details are processed here
    :param container_image_id:
    :param tab:
    :return:
    """
    search_string = ''
    filter_string = ''

    # only process if there was a valid container involved
    if container_images_cache.container_images.get(container_image_id):
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
        # get single requested repository
        container_image = container_images_cache.container_images[container_image_id]
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
                               container_image_id=container_image_id,
                               container_image_TABS=container_image_TABS,
                               is_htmx=is_htmx(),
                               search_string=search_string,
                               filter_string=filter_string,
                               tab=tab_selected)
    return redirect('/')
