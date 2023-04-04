# miscellaneous small stuff

from pathlib import Path
from re import IGNORECASE, \
    sub

from flask import Blueprint, \
    request

# take name for blueprint from file for flawless copy&paste
blueprint = Blueprint(Path(__file__).stem, __name__)


def is_htmx():
    """
    check if it was a htmx request
    :return:
    """
    if 'HX-Request' in request.headers:
        return True
    else:
        return False

@blueprint.app_template_filter('highlight')
def highlight_filter(string, highlight_string):
    """
    highlight a port of the string to be used in search + filter
    :param string:
    :param highlight_string:
    :return:
    """
    if highlight_string:
        # class highlight has to be defined in CSS
        return sub(highlight_string, f'<span class="highlight">{highlight_string}</span>', string, flags=IGNORECASE)
    else:
        return string
