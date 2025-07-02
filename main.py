#!/usr/bin/env python3

from sys import exit

from backend.config import config


if __name__ == '__main__':
    if config.mode == 'collect':
        from backend.collect import run_collector
        # collect GitLab container repository info by interval
        run_collector()
    elif config.mode == 'web':
        from frontend.index import app
        # host 0.0.0.0 needed to be reachable from outside the container
        app.run(host='::')
