# treatment of routes for search

from pathlib import Path

from flask import Blueprint, \
    make_response, \
    render_template, \
    request, \
    session

from backend.collect import update_status
from backend.config import config
from backend.database import couchdb

from frontend.misc import is_htmx

SORTABLE_BY = ['name', 'created', 'tag']
SORT_ORDERS = {'up': False, 'down': True}
RESULTS_PER_PAGE = 10

# take name for blueprint from file for flawless copy&paste
blueprint = Blueprint(Path(__file__).stem, __name__)

db = couchdb.get_database_object('container_images')


def process_search_request(request=None, session=None, search_string: str = ''):
    """
    prepare for search string in container images
    :param request:
    :param session:
    :param search_string:
    :return:
    """
    search_results = dict()
    # 'sort_by' is either set by request or found in session and decides the property to sort by
    if not request.args.get('sort_by'):
        if session.get('sort_by'):
            sort_by = session['sort_by']
        else:
            sort_by = SORTABLE_BY[0]
            session['sort_by'] = sort_by
    elif request.args.get('sort_by') in SORTABLE_BY:
        sort_by = request.args['sort_by']
        session['sort_by'] = sort_by
    elif session.get('sort_by'):
        sort_by = session['sort_by']
    else:
        sort_by = SORTABLE_BY[0]
        session['sort_by'] = sort_by
    # 'sort_order' is either set by request or found in session and may be ascending or descending
    if not request.args.get('sort_order'):
        if session.get('sort_order'):
            sort_order = session['sort_order']
        else:
            sort_order = list(SORT_ORDERS.keys())[0]
            session['sort_order'] = sort_order
    elif request.args.get('sort_order') in SORT_ORDERS.keys():
        sort_order = request.args['sort_order']
        session['sort_order'] = sort_order
    elif session.get('sort_order'):
        sort_order = session['sort_order']
    else:
        sort_order = list(SORT_ORDERS.keys())[0]
        session['sort_order'] = sort_order
    # clean up search string
    if request.form.get('search') or request.form.get('search') == '':
        # to be refined
        search_string = request.form['search'].strip().lower()
    # add matching container_images to search results

    # for name, container_image in container_images_cache.index_by_name.items():
    #     if search_string.lower() in name.lower():
    #         search_results.update({name: container_image})

    search_results_db = db.find(selector={'name': {'$regex': f'.*{search_string.lower()}.*'}}, use_index='name')

    if isinstance(search_results_db, list):
        # sort by sort_order
        search_results_sorted = dict(sorted( { x.get('name'): x for x in search_results_db }.items(),
                                            key=lambda x: x[1][sort_by],
                                            reverse=SORT_ORDERS.get(sort_order)))
    else:
        search_results_sorted = dict()

    # take only sorted values as list
    search_results_list = list(search_results_sorted.values())
    # count number of results
    search_results_count = len(search_results_list)
    # paginate_search_results() delivers page-related information and paginated list of results
    search_results_list_paginated, page, pages_count = paginate_search_results(request, search_results_list)

    return search_string, search_results_list_paginated, search_results_count, page, pages_count


def paginate_search_results(request=None, search_results: list = None):
    """
    cut search result into pieces aka pages
    :param request:
    :param search_results:
    :return:
    """
    pages_count = (len(search_results) // RESULTS_PER_PAGE) + 1
    if not request.args.get('page'):
        page = 1
    else:
        try:
            page = int(request.args['page'])
        except ValueError:
            page = 1

    search_results_paginated = search_results[(page - 1) * RESULTS_PER_PAGE:page * RESULTS_PER_PAGE]

    return search_results_paginated, page, pages_count


@blueprint.route('/<part1>/<part2>/<part3>/<part4>/<part5>/', methods=['GET'])
@blueprint.route('/<part1>/<part2>/<part3>/<part4>/<part5>', methods=['GET'])
@blueprint.route('/<part1>/<part2>/<part3>/<part4>/', methods=['GET'])
@blueprint.route('/<part1>/<part2>/<part3>/<part4>', methods=['GET'])
@blueprint.route('/<part1>/<part2>/<part3>/', methods=['GET'])
@blueprint.route('/<part1>/<part2>/<part3>', methods=['GET'])
@blueprint.route('/<part1>/<part2>/', methods=['GET'])
@blueprint.route('/<part1>/<part2>', methods=['GET'])
@blueprint.route('/<part1>/', methods=['GET'])
@blueprint.route('/<search_string>', methods=['GET', 'POST'])
@blueprint.route('/', methods=['GET', 'POST'])
def search(search_string: str = '', part1: str = '', part2: str = '', part3: str = '', part4: str = '',
           part5: str = ''):
    """
    Search requests - either with single search_strings or whole paths
    """
    # when no searchstring was transmitted try if a '/'-containing path was searched for
    if not search_string:
        parts = [part1, part2, part3, part4, part5]
        search_string = '/'.join([x for x in parts if x])
        # '/' can be part of search_string but will be cut by route handling so add it here again
        # only if at least one part contains anything
        if any(parts) and request.base_url.endswith('/'):
            search_string += '/'
    # for pagination the request will be processed and the result split into page pieces
    search_string, search_results, search_results_count, page, pages_count = process_search_request(request, session,
                                                                                                    search_string)
    # modes 'sort' and 'scroll' are used for sorting of results and paginated infinite scroll
    # otherwise the default whole index will be shown
    if not request.args.get('mode') or request.args.get('mode') not in ['sort', 'scroll']:
        template = '/search/index.html'
    else:
        template = '/search/results.html'

    # use Response to add URL for browser historx via header
    response = make_response(render_template(template,
                                             is_htmx=is_htmx(),
                                             gitlab_url=config.api.url,
                                             page=page,
                                             pages_count=pages_count,
                                             search_string=search_string,
                                             search_results=search_results,
                                             search_results_count=search_results_count,
                                             session=session,
                                             SORTABLE_BY=SORTABLE_BY,
                                             SORT_ORDERS=SORT_ORDERS,
                                             update_status=update_status))
    # htmx header allows to modify browser history
    response.headers['HX-Push-Url'] = f'/search/{search_string}'
    return response
