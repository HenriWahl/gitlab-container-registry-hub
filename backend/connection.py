from requests import Session

from backend.config import config

# gitlab_session to be used to connect to GitLab
gitlab_session = Session()
gitlab_session.headers.update({'PRIVATE-TOKEN': config.api.token})

# disable TLS verification if configured
if config.api.get('verify') == False:
    gitlab_session.verify = False