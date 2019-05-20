import logging
import sys

import server
#import chunk

class serverTracker(object):  # {{{
    def __init__(self):
        self.id2server    = dict()
        self.notRepairing = list()
        self.repairing    = list()

    def get(self, hid):
        svc, chunks = self.id2server[hid]
        return svc, chunks

    def clear(self, hid):
        if self.id2server.__contains__(hid):
            self.id2server[hid][1] = 0
            if self.id2server[hid][0] in self.notRepairing:
                self.notRepairing.remove(self.id2server[hid][0])
            elif self.id2server[hid][0] in self.repairing:
                self.repairing.remove(self.id2server[hid][0])

    def addChunk(self, hid):
        if self.id2server.__contains__(hid):
            self.id2server[hid][1] += 1

    def add(self, svc):
        assert svc not in self.id2server, print(svc, self.id2server)
        self.id2server[svc.hid] = [svc, 0]
        #svc.recovering()

    def chunking(self, svc):
        assert svc not in self.repairing
        self.id2server[svc.hid][1] += 1
    
    def callRepair(self, svc):
        #print('Test call repair: svc{:d}'.format(svc.hid))
        #print(self.id2server)
        assert svc not in self.id2server
        # clear the chunks
        self.clear(svc.hid)

        self.notRepairing.append(svc)

    
    def setRecovering(self, svc):
        #assert svc in self.notRepairing
        self.repairing.append(svc)
        if svc in self.notRepairing:
            self.notRepairing.remove(svc)
        svc.recovering()

    
    def setComplete(self, svc):
        assert svc in self.repairing
        self.repairing.remove(svc)
        svc.complete()
 

    def delete(self, svc):
        assert svc.hid in self.id2server
        del self.id2server[svc.hid]

    def __str__(self):
        txt = ''
        for item in self.id2server:
            txt += '{:d}\n'.format(int(item))
        return 'ServerTracker: {}'.format(txt)
# }}}