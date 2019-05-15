import logging
import sys
import numpy as np

import env

STATUS_CHUNKING = env.STATUS_CHUNKING
STATUS_NO_CHUNK = env.STATUS_NO_CHUNK
STATUS_COMPLETE = env.STATUS_COMPLETE
STATUS_SHUTDOWN = env.STATUS_SHUTDOWN
STATUS_FAIL     = env.STATUS_FAIL

# Secure and shut-down devices are handled without in-memory objects.
class Server(object):  # {{{
    @staticmethod
    def bootup(params):
        if (len(params) == 3):
            hid     = params[0]
            status  = params[1]
            statusB = params[2]
        elif (len(params) == 2):
            hid     = params[0]
            status  = params[1]
            statusB = STATUS_SHUTDOWN
        elif(len(params)== 1):
            hid     = params[0]
            status  = STATUS_NO_CHUNK
            statusB = STATUS_SHUTDOWN
        server = Server(hid, status)

        upTime   = env.func_server_up_time()
        failTime = env.func_server_fail_time()
        logging.info('hid:%d up_time:%f fail_time:%f', hid, upTime, failTime)
        #env.server_tracker.add(server)

        if failTime < upTime:
            server.next_failtime = env.now + failTime
            ev = (env.now + failTime, server.fail, [hid])
            env.enqueue(ev)

        server.next_downtime = env.now + upTime
        ev = (env.now + upTime, server.shutdown, [hid])
        env.enqueue(ev)
        
        env.add_bootup_server(hid, status, statusB)
        env.server_tracker.add(server) # pylint: disable=no-member
        

    def __init__(self, hid, status):
        self.hid            = hid
        self.status         = status
        self.next_downtime  = 0
        self.next_failtime  = 0
        self.fail_time      = 0
        self.fail_time_tot  = 0
        self.chunks         = 0
        self.bot            = None

    def retry(self):
        logging.debug('hid:%d retry start', self.hid)
        assert self.next_downtime > 0
        recoveryTime = env.func_server_recovery_time()  # pylint: disable=not-callable

        if (env.now + recoveryTime) < self.next_downtime:
            ev = (env.now + recoveryTime, env.server_tracker.chunking, self)   # pylint: disable=no-member
            env.enqueue(ev)
        #env.server_tracker.delete(self)

    def fail(self, _none):
        logging.debug('hid:%d fail', self.hid)
        assert self.next_downtime > 0 
        env.add_fail_server(self.hid, self.status)
        recoveryTime = env.func_server_recovery_time()  # pylint: disable=not-callable
        self.fail_time = env.now
        self.status = STATUS_FAIL
        self.next_failtime = 0

        if (env.now + recoveryTime) < self.next_downtime:
            ev = (env.now + recoveryTime, env.server_tracker.chunking, self)   # pylint: disable=no-member
            env.enqueue(ev)
        #env.server_tracker.delete(self)

    def recovering(self, _none):
        logging.debug('hid:%d recovering', self.hid)
        assert self.next_downtime > 0
        env.add_chunking_server(self.hid, self.status)

        self.status = STATUS_CHUNKING

        chunkTime = env.func_repair_chunk_time() # pylint: disable=not-callable
        if (env.now + chunkTime) < self.next_downtime:
            ev = (env.now + chunkTime, env.server_tracker.chunking, self)  # pylint: disable=no-member
            env.enqueue(ev)

    def recovery(self, _none):
        logging.debug('hid:%d recovery', self.hid)
        assert self.next_downtime > 0
        assert self.fail_time > 0
        assert self.status == STATUS_CHUNKING
        env.add_bootup_server(self.hid, STATUS_COMPLETE, self.status)

        failTime = env.func_server_fail_time()
        self.fail_time_tot += env.now - self.fail_time
        self.fail_time = 0

        if (env.now + failTime) < self.next_downtime:
            self.next_failtime = env.now + failTime
            ev = (env.now + failTime, self.fail, [self.hid])
            env.enqueue(ev)
        #env.server_tracker.delete(self)
        
        self.status = STATUS_COMPLETE

    def shutdown(self, _none):
        logging.debug('hid:%d shutdown', self.hid)
        assert self.status == STATUS_FAIL or self.status == STATUS_NO_CHUNK or self.status == STATUS_CHUNKING or self.status == STATUS_COMPLETE
        if self.status == STATUS_FAIL:
            assert self.fail_time > 0
            self.fail_time_tot += env.now - self.fail_time
            self.fail_time = 0

        
        off_time = env.func_server_down_time()  # pylint: disable=not-callable
        ev = (env.now + off_time, Server.bootup, [self.hid, STATUS_NO_CHUNK, STATUS_SHUTDOWN])
        env.enqueue(ev)

        env.add_shutdown_server(self.hid, self.status)
        self.status = STATUS_SHUTDOWN
        env.server_tracker.delete(self) # pylint: disable=no-member