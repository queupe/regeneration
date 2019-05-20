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
    def startup(params):
        # start a new server - it enter in operation
        if (len(params) == 4):
            hid     = params[0]
            status  = params[1]
            statusB = params[2]
        elif (len(params) == 3):
            hid     = params[0]
            status  = params[1]
            statusB = STATUS_SHUTDOWN
        elif(len(params)== 2):
            hid     = params[0]
            status  = STATUS_NO_CHUNK
            statusB = STATUS_SHUTDOWN

        logging.info('Server started hid:%d, status:%d status bef:%d', hid, status, statusB)
        
        server = Server(hid, statusB)
        server.bootup([status, statusB,'Inicialização'])
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

    def bootup(self, params):
        logging.debug('Server bootup hid:%d, status bef:%d', self.hid, self.status)
        # reload a shutdown server
        if (len(params) == 1):
            status  = STATUS_NO_CHUNK
            statusB = STATUS_SHUTDOWN
        elif(len(params)== 2):
            status  = params[0]
            statusB = STATUS_SHUTDOWN
        elif(len(params)== 3):
            status  = params[0]
            statusB = params[1]

        # the actived server can fail or shutdown
        upTime   = env.func_server_up_time()
        failTime = env.func_server_fail_time()
        logging.debug('Server hid:%d, downtime:%f, fail_time:%f', self.hid, env.now + upTime, env.now + failTime)
        
        if failTime < upTime:
            self.next_failtime = env.now + failTime
            ev = (env.now + failTime, self.fail, [self.hid, 'Queue server hid:{:d}, fail at {:f}'.format(self.hid, self.next_failtime)])
            env.enqueue(ev)

        # Include event to turn down
        self.next_downtime = env.now + upTime
        ev = (env.now + upTime, self.shutdown, [self.hid, 'Queue server hid:{:d},  shutdown at {:f}'.format(self.hid, self.next_downtime)])
        env.enqueue(ev)
        
        self.status = status

        env.add_bootup_server(self.hid, status, statusB)
        env.server_tracker.callRepair(self) # pylint: disable=no-member
        

    def fail(self, _none):
        logging.debug('Server fail hid:%d, status bef:%d', self.hid, self.status)
        assert self.next_downtime > 0 
        assert self.next_failtime > 0
        assert self.isActived(), "{}, {}".format(self.hid, self.status)

        if self.isActived():
            env.add_fail_server(self.hid, self.status)
            # recoveryTime = env.func_server_recovery_time()  # pylint: disable=not-callable
            if self.fail_time > 0:
                self.fail_time_tot += env.now - self.fail_time
            self.fail_time = env.now
            self.status = STATUS_FAIL
            self.next_failtime = 0

        env.server_tracker.callRepair(self) # pylint: disable=no-member

    def recovering(self):
        logging.debug('Server recovering hid:%d, status bef:%d', self.hid, self.status)
        assert self.next_downtime > 0

        if self.status == STATUS_FAIL or self.status == STATUS_NO_CHUNK:

            env.add_chunking_server(self.hid, self.status)

            # Checking if is need to include fail event
            if self.status == STATUS_FAIL:
                failTime = env.func_server_fail_time()
                if (env.now + failTime) < self.next_downtime:
                    logging.debug('Server hid:%d, downtime:%f, new failtime:%f', self.hid, self.next_downtime, env.now + failTime)
                    self.next_failtime = env.now + failTime
                    ev = (env.now + failTime, self.fail, [self.hid, 'Queue fail at {:f}'.format(self.next_failtime)])
                    env.enqueue(ev)            

            self.status = STATUS_CHUNKING

    def complete(self):
        logging.debug('Server completed hid:%d, status bef:%d', self.hid, self.status)
        assert self.next_downtime > 0
        assert self.status == STATUS_CHUNKING

        # Control the time in fail
        if self.fail_time > 0:
            self.fail_time_tot += env.now - self.fail_time
        self.fail_time = 0

        env.add_bootup_server(self.hid, STATUS_COMPLETE, self.status)

        self.status = STATUS_COMPLETE

    def shutdown(self, _none):
        logging.debug('Server shutdown hid:%d, status bef:%d', self.hid, self.status)
        if self.isUp():

            if self.status == STATUS_FAIL:
                self.fail_time_tot += env.now - self.fail_time
            self.fail_time = 0
            
            # include event to turn ON
            off_time = env.func_server_down_time()  # pylint: disable=not-callable
            ev = (env.now + off_time, self.bootup, [STATUS_NO_CHUNK, STATUS_SHUTDOWN, 'Queue server hid:{:d}, bootup at {:f}'.format(self.hid, env.now + off_time)])
            env.enqueue(ev)

            env.add_shutdown_server(self.hid, self.status)
            self.status = STATUS_SHUTDOWN
            env.server_tracker.clear(self.hid) # pylint: disable=no-member
    
    def isActived(self):
        return self.status == STATUS_NO_CHUNK or self.status == STATUS_CHUNKING or self.status == STATUS_COMPLETE

    def isNotActived(self):
        return self.status == STATUS_SHUTDOWN or self.status == STATUS_FAIL

    def isUp(self):
        return self.status == STATUS_NO_CHUNK or self.status == STATUS_CHUNKING or self.status == STATUS_COMPLETE or self.status == STATUS_FAIL

    def isDown(self):
        return self.status == STATUS_SHUTDOWN