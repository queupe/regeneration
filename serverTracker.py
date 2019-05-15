import logging
import sys

import server
#import chunk

class serverTracker(object):  # {{{
    def __init__(self):
        self.id2server = dict()

    def get(self, sid):
        svc, chunks = self.id2server[sid]
        return svc, chunks

    def add(self, svc):
        assert svc not in self.id2server
        self.id2server[svc.hid] = [svc, 0]
        svc.recovering()

    def chunking(self, svc):
        assert svc in self.id2server
        self.id2server[svc.hid][1] += 1
 
    def delete(self, svc):
        assert svc.hid in self.id2server
        del self.id2server[svc.hid]

    def __str__(self):
        txt = ''
        for item in self.id2server:
            txt += '{:d}\n'.format(int(item))
        return 'ServerTracker: {}'.format(txt)
# }}}