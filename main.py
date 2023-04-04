#!/usr/bin/env python3

from backend.collect import CollectorThread
from frontend.index import app

if __name__ == '__main__':
    # collect GitLab container repository info by interval as thread in the background
    collector_thread = CollectorThread()
    collector_thread.start()

    # host 0.0.0.0 needed to be reachable from outside the container
    app.run(host='0.0.0.0')