# -*- coding: UTF-8 -*-
from log_client import LogStatClient

__author__ = 'xing'


class LogStatServer():
    def __init__(self, source_file):
        self.source_file = source_file
        self.client = list()

    def register(self, log_stat_client):
        if isinstance(log_stat_client, LogStatClient):
            self.client.append(log_stat_client)
        else:
            raise ValueError, 'must be LogStatServer object'

    def unregister(self, log_stat_client):
        if isinstance(log_stat_client, LogStatServer):
            self.client.remove(log_stat_client)

    def clear_register(self):
        self.client = list()

    def run(self):
        for line in self.source_file.readlines():
            line = line.strip()
            for call in self.client:
                if not call.on_change(line):
                    break

    def stat_result(self):
        result = list()
        index = 0
        for c in self.client:
            li = c.get_result()
            if li:
                index += 1
                li[0] = '\t%d. %s' % (index, li[0].lstrip())
                result.extend(li)
        return result
