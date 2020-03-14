#!/usr/bin/env python3
import requests
import datetime
import pprint


pp = pprint.PrettyPrinter(indent=4)


class CTFTime:

    def __init__(self, limit=10, start=int(datetime.datetime.today().timestamp()), finish=int((datetime.datetime.today() + datetime.timedelta(days=7)).timestamp())):
        self.limit = limit
        self.start = start
        self.finish = finish
    
    @property
    def upcoming_ctfs(self):
        response = requests.get('https://ctftime.org/api/v1/events/',
                    params={'limit': self.limit, 'start': self.start, 'finish': self.finish},
                    headers = {
                        'User-Agent': 'curl/7.58.0', 
                        'Host': 'ctftime.org',
                        })
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception('CTFTime', 'Could not get upcoming ctfs')