from pathlib import Path

from flask import Blueprint, \
    redirect, \
    request, \
    render_template, \
    render_template_string

from backend.collect import update_status

from frontend.misc import is_htmx

# take name for blueprint from file for flawless copy&paste
blueprint = Blueprint(Path(__file__).stem, __name__)

@blueprint.route('/progress')
def progress():
    if is_htmx():
        return render_template('health/progress.html',
                                update_status=update_status)
    else:
        return redirect('/search/')
