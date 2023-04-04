# central index /

from secrets import token_hex

from time import time

from flask import Flask, \
    redirect, \
    render_template_string

from backend.collect import update_status

from frontend.container_image import blueprint as container_image_blueprint
from frontend.health import blueprint as health_blueprint
from frontend.search import blueprint as search_blueprint
from frontend.misc import blueprint as misc_blueprint

app = Flask(__name__)

# as there is no further session management the secret key might be regenerated with every new start
app.secret_key = token_hex()

# add timestamp to jinja-globals
app.jinja_env.globals.update(timestamp=int(time()))

# add blueprint routes
app.register_blueprint(container_image_blueprint, url_prefix='/container_image')
app.register_blueprint(health_blueprint, url_prefix='/health')
app.register_blueprint(search_blueprint, url_prefix='/search')
app.register_blueprint(misc_blueprint)


@app.errorhandler(404)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    # catch all and redirect to search
    return redirect('/search/')
