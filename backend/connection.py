from ssl import PROTOCOL_TLS_CLIENT

from httpx import Client, Response
from truststore import SSLContext

from backend.config import config, \
    TIMEOUT
from backend.helpers import log

# disable TLS verification if configured
if config.api.get('verify', True) == False:
    verify = False
else:
    # use system trust store for TLS verification
    verify = SSLContext(PROTOCOL_TLS_CLIENT)
gitlab_session = Client(follow_redirects=True, verify=verify)

# add GitLab API token to session headers
# this is needed for all requests to the GitLab API
gitlab_session.headers.update({'PRIVATE-TOKEN': config.api.token})


def gitlab_session_get(url, params=None) -> Response:
    """
    GET request to GitLab API with session - important with exception handling
    :param url: URL to request
    :param params: optional parameters for the request
    :return: response object
    """
    try:
        return gitlab_session.get(url, params=params, timeout=TIMEOUT)
    except Exception as exception:
        # if an exception occurs, return a response with status code 999 to indicate an unknown error
        log.error(f'Exception during access to GitLab: {exception}')
        return Response(999, text=str(exception))
