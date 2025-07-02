from pathlib import Path

from flask import Blueprint, \
    redirect, \
    render_template

from frontend.misc import is_htmx

# take name for blueprint from file for flawless copy&paste
blueprint = Blueprint(Path(__file__).stem, __name__)

@blueprint.route('/progress')
def progress():
    if is_htmx():
        return render_template('health/progress.html')
    else:
        return redirect('/search/')
