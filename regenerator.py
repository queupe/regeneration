import logging
import random
import math

import server
import serverTracker

import env

class Repair(object): # {{{
    def __init__(self):
        self.c1    = env.repair_cost_activ
        self.c2    = env.repair_cost_chunk
        self.B     = env.chunk_size
        self.n     = env.chunk_n
        self.k     = env.chunk_k
        self.d     = env.chunk_d        
# class Repair }}}

class MBRrepair(object):  # {{{
    def __init__(self):
        #logging.debug('%s rate %f', self, self.rate)
        self.c1    = env.repair_cost_activ
        self.c2    = env.repair_cost_chunk
        self.B     = env.chunk_size
        self.n     = env.chunk_n
        self.k     = env.chunk_k
        self.d     = env.chunk_d
        self.alpha = math.ceil(2 * self.d * self.B / (self.k * (2 * self.d - self.k + 1)))
        self.beta  = math.ceil(2 *          self.B / (self.k * (2 * self.d - self.k + 1)))

    def activate(self, params):

        if len(env.server_tracker.notRepairing) > 0 and env.count_complete + env.count_chunking <= self.n :
            svc = env.server_tracker.notRepairing.pop(0)
            env.server_tracker.setRecovering(svc)
            env.add_activation(svc.hid, self.c1, 0.0)

            chunkTime = env.now + env.func_repair_chunk_time()
            ev = (chunkTime, self.requestChunk, [svc, chunkTime, 'Queue request chunk:{:d}, at {:f}, Server:{:d}'.format(1, chunkTime, svc.hid)])
            env.enqueue(ev)
        
        timeActivate = env.now + env.func_server_recovery_time()
        ev = (timeActivate, self.activate, ['Queue next activated (no server) at:{:f}'.format(timeActivate)])
        env.enqueue(ev)

    def addChunk(self, params):
        assert len(params) == 1
        svc = params[0]

        env.server_tracker.addChunk(svc.hid)
        _serv, chuncks = env.server_tracker.get(svc.hid)

        if chuncks >= self.d:
            env.server_tracker.setComplete(svc)


        env.add_chunk(svc.hid, 0.0, self.beta * self.c2)

    def requestChunk(self, params):
        assert len(params) == 3
        svc          = params[0]
        _oldChunkTime = params[1]
        chunkTime = env.now + env.func_repair_chunk_time()

        self.addChunk([svc])

        chunks = env.server_tracker.id2server[svc.hid][1]

        if svc.status == env.STATUS_CHUNKING:
            if chunkTime < svc.next_failtime and chunkTime < svc.next_downtime:
                ev = (chunkTime, self.requestChunk, [svc, chunkTime, 'Queue request chunk:{:d}, at {:f}, Server:{:d}'.format(chunks, chunkTime, svc.hid)])
                env.enqueue(ev)

# }}}
