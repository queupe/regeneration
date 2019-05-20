import heapq
import json
import random
import logging
import argparse

# ========================================================
# Define the constants
DIST_EXPONENTIAL = 'EXPONENTIAL'
DIST_UNIFORM     = 'UNIFORM'
DIST_GAUSSIAN    = 'GAUSSIAN'
DIST_CONSTANT    = 'CONSTANT'

STATUS_SHUTDOWN = 0
STATUS_NO_CHUNK = 10
STATUS_CHUNKING = 11
STATUS_COMPLETE = 12
STATUS_FAIL     = 20
STATUS_STARTED  = 30

# ========================================================
# Define auxiliary functions
# Function to parse the input call
def create_parser():  # {{{
    desc = '''Repair simulator'''

    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('--config-json',
                        dest='configfn',
                        action='store',
                        metavar='FILE',
                        type=str,
                        required=True,
                        help='JSON file containing simulation configuration')

    return parser
# }}}

# Function to select and parser the distribuition
def parse_dist(param, dist):  # {{{
    #logging.info('%s: %s', dist, param)
    
    if dist.upper() == DIST_EXPONENTIAL:
        assert len(param) >= 1
        fn = lambda: abs(random.expovariate(float(param[0])))
    elif dist.upper() == DIST_UNIFORM:
        assert len(param) >= 2
        fn = lambda: abs(random.uniform(float(param[0]), float(param[1])))
    elif dist.upper() == DIST_GAUSSIAN:
        assert len(param) >= 2
        fn = lambda: abs(random.gauss(float(param[0]), float(param[1])))
    elif dist.upper() == DIST_CONSTANT:
        assert len(param) >= 1
        fn = lambda: abs(float(param[0]))
    #else:
        #logging.fatal('error passing distribution %s', param)
        #raise ValueError('error parsing distribution %s' % param)
    average = sum(fn() for _ in range(1000))/1000.0
    #logging.debug('1000 samples with average %f', average)
    return fn
    
# }}}

#class SimulationTimeFilter(logging.Filter):  # {{{
#    def filter(self, record):
#        record.TIME = now
#        return True
# }}}

# ========================================================
# Define enviroment callable

now = 0
evqueue = list()
evseq = 0

config = dict()

maxid   = 0
endtime = 0.0

chunk_k    = 0
chunk_d    = 0
chunk_n    = 0
chunk_size = 0

repair_class      = None
repair_cost_activ = None
repair_cost_chunk = None

hist = list()
count_chunking  = 0
count_no_chunk  = 0
count_complete  = 0
count_shutdown  = 0
count_fail      = 0
count_started   = 0

hist_repair      = list()
count_activation = 0
count_get_chunk  = 0
cost1_total      = 0.0
cost2_total      = 0.0

server_tracker = None

func_server_up_time       = None
func_server_down_time     = None
func_server_fail_time     = None
func_server_recovery_time = None

func_repair_chunk_time    = None

# ========================================================
# Define execution functions

def start(conf):
    
    global now
    global evqueue
    global evseq
    global config

    global maxid
    global endtime

    global chunk_k
    global chunk_d
    global chunk_n
    global chunk_size

    global repair_class
    global repair_cost_activ
    global repair_cost_chunk

    global hist
    global count_chunking  
    global count_no_chunk  
    global count_complete  
    global count_shutdown  
    global count_fail

    global hist_repair
    global count_activation
    global count_get_chunk
    global cost1_total
    global cost2_total

    global server_tracker

    global func_server_up_time
    global func_server_down_time
    global func_server_fail_time
    global func_server_recovery_time

    global func_repair_chunk_time
    
    
    now     = 0
    evqueue = list()
    evseq   = 0
    
    config = conf
    

    maxid      = config['max_id']
    endtime    = config['endtime']
     
    chunk_k    = config['chunk']['recovery']
    chunk_d    = config['chunk']['repair']
    chunk_n    = config['chunk']['total']
    chunk_size = config['chunk']['size']
    
    repair_class      = config['repair']['class']
    repair_cost_activ = config['repair']['activate_cost']
    repair_cost_chunk = config['repair']['transfer_cost']

    
    func_server_up_time   = parse_dist(config['server']['up_rate_param'],
                                       config['server']['up_rate_distr'])
    
    func_server_down_time = parse_dist(config['server']['shutdown_rate_param'],
                                       config['server']['shutdown_rate_distr'])
    func_server_fail_time = parse_dist(config['server']['fail_rate_param'],
                                       config['server']['fail_rate_distr'])
    
    func_server_recovery_time = parse_dist(config['repair']['activate_rate_param'],
                                       config['repair']['activate_rate_distr'])
    func_repair_chunk_time = parse_dist(config['repair']['transfer_rate_param'],
                                       config['repair']['transfer_rate_distr'])

    hist            = list()
    count_chunking  = 0
    count_no_chunk  = 0
    count_complete  = 0
    count_shutdown  = 0
    count_fail      = 0

    hist_repair      = list()
    count_activation = 0
    count_get_chunk  = 0
    cost1_total      = 0.0
    cost2_total      = 0.0
    

def recovery_server(hid):
    if random.random() < config['frac_repair']:
        return True
    else:
        return False

def enqueue(ev):
    global now
    # Assumes ev = (time, fn, fndata)
    if ev[0] < now:
        print(ev[0],now)
    assert ev[0] >= now
    global evseq
    heapq.heappush(evqueue, (ev[0], evseq, ev[1], ev[2]))
    evseq += 1

def dequeue():
    global now
    now, _evseq, fn, data = heapq.heappop(evqueue)
    return (now, fn, data)

def add_bootup_server(hid, status=STATUS_NO_CHUNK, statusB=STATUS_SHUTDOWN):
    global hist
    global count_chunking  
    global count_no_chunk  
    global count_complete  
    global count_shutdown  
    global count_fail

    insert_hist = True
    if statusB == STATUS_STARTED:
        insert_hist = True


    if status == STATUS_CHUNKING:
        count_chunking += 1
    elif status == STATUS_NO_CHUNK:
        count_no_chunk += 1
    elif status == STATUS_COMPLETE:
        count_complete += 1


    if statusB == STATUS_CHUNKING and count_chunking > 0:
        count_chunking -= 1
    elif statusB == STATUS_NO_CHUNK and count_no_chunk > 0:
        count_no_chunk -= 1
    elif statusB == STATUS_COMPLETE and count_complete > 0:
        count_complete -= 1
    elif statusB == STATUS_SHUTDOWN and count_shutdown > 0:
        count_shutdown -= 1
    elif statusB == STATUS_FAIL and count_fail > 0:
        count_fail -=1
    
    if insert_hist:
        hist.append([now, hid, statusB, status, count_chunking , count_no_chunk, count_complete, count_shutdown,count_fail])

def add_fail_server(hid, status):
    global hist
    global count_chunking  
    global count_no_chunk  
    global count_complete  
    global count_shutdown  
    global count_fail      

    count_fail += 1
    if status == STATUS_CHUNKING and count_chunking > 0:
        count_chunking -= 1
    elif status == STATUS_NO_CHUNK and count_no_chunk > 0:
        count_no_chunk -= 1
    elif status == STATUS_COMPLETE and count_complete > 0:
        count_complete -= 1

    hist.append([now, hid, status, STATUS_FAIL, count_chunking , count_no_chunk, count_complete, count_shutdown,count_fail])

def add_chunking_server(hid, status=STATUS_SHUTDOWN):
    global hist
    global count_chunking  
    global count_no_chunk  
    global count_complete  
    global count_shutdown  
    global count_fail      

    count_chunking += 1
    if status == STATUS_CHUNKING and count_chunking > 0:
        count_chunking -= 1
    elif status == STATUS_NO_CHUNK and count_no_chunk > 0:
        count_no_chunk -= 1
    elif status == STATUS_COMPLETE and count_complete > 0:
        count_complete -= 1
    elif status == STATUS_SHUTDOWN and count_shutdown > 0:
        count_shutdown -= 1
    elif status == STATUS_FAIL and count_fail > 0:
        count_fail -= 1

    hist.append([now, hid, status, STATUS_CHUNKING, count_chunking , count_no_chunk, count_complete, count_shutdown,count_fail])

def add_shutdown_server(hid, status):
    global hist
    global count_chunking  
    global count_no_chunk  
    global count_complete  
    global count_shutdown  
    global count_fail      

    count_shutdown += 1
    if status == STATUS_CHUNKING and count_chunking > 0:
        count_chunking -= 1
    elif status == STATUS_NO_CHUNK and count_no_chunk > 0:
        count_no_chunk -= 1
    elif status == STATUS_COMPLETE and count_complete > 0:
        count_complete -= 1
    elif status == STATUS_FAIL and count_fail > 0:
        count_fail -= 1

    hist.append([now, hid, status, STATUS_SHUTDOWN, count_chunking , count_no_chunk, count_complete, count_shutdown,count_fail])

def add_complete_server(hid, status=STATUS_CHUNKING):
    global hist
    global count_chunking  
    global count_no_chunk  
    global count_complete  
    global count_shutdown  
    global count_fail      

    count_complete += 1
    if status == STATUS_CHUNKING and count_chunking > 0:
        count_chunking -= 1

    hist.append([now, hid, status, STATUS_SHUTDOWN, count_chunking , count_no_chunk, count_complete, count_shutdown,count_fail])

def add_activation(hid, cost1, cost2):
    global hist_repair
    global count_activation
    global count_get_chunk
    global cost1_total
    global cost2_total

    count_activation += 1
    cost1_total      += cost1

    hist_repair.append([now, hid, count_activation, count_get_chunk, cost1_total, cost2_total])

def add_chunk(hid, cost1 , cost2):
    global hist_repair
    global count_activation
    global count_get_chunk
    global cost1_total
    global cost2_total

    count_get_chunk += 1
    cost2_total     += cost2

    hist_repair.append([now, hid, count_activation, count_get_chunk, cost1_total, cost2_total])
