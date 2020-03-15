#!/usr/bin/env python3
import time
import datetime

import requests
import pprint

DEFAULT_DELTA = datetime.timedelta(days=7).total_seconds()
pp = pprint.PrettyPrinter(indent=4)


class CTFTime:

    def __init__(self, limit=10, start=time.time(), finish=time.time() + DEFAULT_DELTA):
        self.limit = limit
        self.start = int(start)
        self.finish = int(finish)
    
    @property
    def upcoming_ctfs(self):
        params = {'limit': self.limit,
                  'start': self.start,
                  'finish': self.finish}
        headers = {'User-Agent': 'curl/7.58.0',
                   'Host': 'ctftime.org'}

        response = requests.get('https://ctftime.org/api/v1/events/',
                                params=params,
                                headers=headers)

        assert response.status_code == 200, "Could not get upcoming ctfs"

        return response.json()

if __name__ == '__main__':
    ctftime = CTFTime()
    pp.pprint(ctftime.upcoming_ctfs)
