from httpx import Client

from backend.config import config

# gitlab_session to be used to connect to GitLab
gitlab_session = Client(follow_redirects=True)
gitlab_session.headers.update({'PRIVATE-TOKEN': config.api.token})

# disable TLS verification if configured
if config.api.get('verify', True) == False:
    gitlab_session = Client(follow_redirects=True, verify=False)
else:
    gitlab_session = Client(follow_redirects=True)

gitlab_session.headers.update({'PRIVATE-TOKEN': config.api.token})