#!/usr/bin/env python3


import importlib
import atexit
import json
import logging
import random
import resource
import sys
import time
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime
from os import path

import env
import server
import serverTracker
import regenerator

#DIR_LOG     = './log/'
DIR_OUTPUT  = './output/'
OUTPUT_FILE  = 'servers'
OUTPUT_COUNT = 'counter'
OUTPUT_CONFG = 'config'
_GRAPH_     = './graph/'

class SimulationTimeFilter(logging.Filter):  # {{{
    def filter(self, record):
        record.TIME = env.now
        return True
# }}}

# COUNTER
def read_counter():
    return json.loads(open("counter.json", "r").read()) + 1 if path.exists("counter.json") else 0

def write_counter():
    with open("counter.json", "w") as f:
        f.write(json.dumps(counter))
counter = read_counter()
atexit.register(write_counter)



def execution (filename_output = DIR_OUTPUT + OUTPUT_FILE, filename_count = DIR_OUTPUT + OUTPUT_COUNT):
    parser = env.create_parser()
    opts   = parser.parse_args()
    #configfn = 'config/test_prime.json'
    conf = None
    with open(opts.configfn, 'r') as fd:
        conf = json.load(fd)

    # inside definitions of enviorment
    env.start(conf)
    
    # outside definitions of enviorment
    env.server_tracker = serverTracker.serverTracker()
    env.repair_manager = regenerator.MBRrepair()

    logfile  = conf.get('logfile', 'log.txt')
    loglevel = getattr(logging, conf.get('loglevel', 'INFO'))
    if loglevel == logging.DEBUG:
        print(loglevel)

    logging.basicConfig(filename=logfile,
                        format='%(TIME)f %(filename)s:%(lineno)d/%(funcName)s %(message)s',
                        level=loglevel,
                        filemode='w')
    logger = logging.getLogger()
    logger.addFilter(SimulationTimeFilter())
    logging.info('%s', json.dumps(conf))

    
    print('Test of distribuition:')
    values = list()
    for i in range(1000):
        one  = env.func_server_up_time()
        values.append(one)
        #print(one)
    print('Distribuition: \'up time\' dist:{} params:{}'.format(
                                        env.config['server']['up_rate_param'],
                                        env.config['server']['up_rate_distr']))
    values = np.array(values)
    print('Result samples:{:d} mean:{:f} std:{:f}'.format(len(values), np.mean(values), np.std(values)))

    print('State:{:d}'.format(int(env.config['chunk']['size'])))

    #servers = list()
    for hid in range(1, env.maxid+1):
        down_time = env.func_server_down_time()
        #if down_time > env.endtime:
        #    print(hid)
        ev = (env.now + down_time, server.Server.startup, [hid, env.STATUS_NO_CHUNK, env.STATUS_STARTED,'Queue create server hid:{:d}, at:{:f}'.format(hid, env.now + down_time)])
        env.enqueue(ev)
    logging.info('created %d bootup events', len(env.evqueue))

    env.repair_manager.activate([])

    #assert (len(sim.evqueue) == (sim.config['maxhid'] // sim.host_tracker.vulnerable_period) + 1)

    while env.evqueue and env.now < env.endtime:
        _now, fn, data = env.dequeue()
        logging.debug('dequeue len %d action(%s)', len(env.evqueue),data[-1])
        fn(data)

    files_results()

    return 0

def files_results(filename_config=OUTPUT_CONFG, filename_output=OUTPUT_FILE, filename_count=OUTPUT_COUNT):
    filename_cfg = '{}sample{:03d}_{}.json'.format(DIR_OUTPUT, counter, filename_config)
    filename_out = '{}sample{:03d}_{}.csv'.format(DIR_OUTPUT, counter, filename_output)
    filename_cnt = '{}sample{:03d}_{}.csv'.format(DIR_OUTPUT, counter, filename_count)

    with open(filename_cfg, 'w') as fd:
        fd.write(json.dumps(env.config))

    with open(filename_out, 'w') as fd:
        fd.write('TIME, ID, ST_B, ST_A, chunking, no_chunk, complete, shutdonw, fail, total\n')
        serves = np.zeros(env.maxid+1, dtype=np.int)
        line = 1
        test = 0
        for item in env.hist:
            total = item[4] + item[5] + item[6] + item[7] + item[8]
            fd.write('{:12.5f}, {:04d}, {:3d}, {:3d}, {:4d}, {:4d}, {:4d}, {:4d}, {:4d}, {:4d}\n'.format(item[0],
                                                                                   item[1],
                                                                                   item[2],
                                                                                   item[3],
                                                                                   item[4],
                                                                                   item[5],
                                                                                   item[6],
                                                                                   item[7],
                                                                                   item[8],
                                                                                   total))
            serves[item[1]] = 1
            if total != int(np.sum(serves)) and test == 0:
                print('Error Total sum:{:d} Total Ids:{:d} ID:{:d} Line:{:d}'.format(
                    total,int(np.sum(serves)), item[1], line))
                print(item)
                test = 1
            line += 1

    with open(filename_cnt, 'w') as fd:
        fd.write('TIME, ID, #cost1, #cost2, cost1, cost2')
        for item in env.hist_repair:
            fd.write('{:12.5f},{:04d}, {:4d}, {:5d}, {:12.5f}, {:12.5f}\n'.format(item[0],
                                                                                  item[1],
                                                                                  item[2],
                                                                                  item[3],
                                                                                  item[4],
                                                                                  item[5]))



def plotting_results():

    logfile ='log_file_{:>03d}.log.txt'.format(counter)
    loglevel = logging.WARNING
    logging.basicConfig(filename=logfile,
                        format='%(message)s',
                        level=loglevel,
                        filemode='w')
    
    info_array = np.array(env.hist)

    plt.plot(info_array[:,0], info_array[:,4]/env.maxid, label='Chunking'    , color='#000055', linestyle = '--')
    plt.plot(info_array[:,0], info_array[:,5]/env.maxid, label='No Chunk'    , color='#000075', linestyle = '--')
    plt.plot(info_array[:,0], info_array[:,6]/env.maxid, label='Complete'    , color='#000095', linestyle = '--')
    on_system = info_array[:,4] + info_array[:,5] + info_array[:,6]
    plt.plot(info_array[:,0], on_system/env.maxid, label='On'    , color='#0000FF')
    
    #plt.plot(range(100), np.ones(100))
    plt.plot(info_array[:,0], info_array[:,7]/env.maxid, label='Shutdown'    , color='r')
    plt.plot(info_array[:,0], info_array[:,8]/env.maxid, label='Fail'        , color='g')
    

    plt.xlabel('Time')
    plt.ylabel('proportion of')
    plt.ylim((0.0,1.7))
    plt.legend(loc='right')
    filename_pdf ='exec_counter-{:>03d}.pdf'.format(counter)
    plt.savefig(_GRAPH_ + filename_pdf)
    plt.show()
    plt.clf()

def main():
    execution()
    return 0

if __name__ == '__main__':
    #start = time.time()
    start_time = datetime.now()
    results = main()
    #end = time.time()
    time_elapsed = datetime.now() - start_time
    print("Time elapsed: {0}".format(time_elapsed))
    sys.exit(results)