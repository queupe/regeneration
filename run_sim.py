#!/usr/bin/env python3


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

DIR_LOG     = './log/'
DIR_OUTPUT  = './output/'
OUTPUT_FILE = 'saida.csv'
_GRAPH_     = './graph/'


def execution (filename_output = DIR_OUTPUT + OUTPUT_FILE):
    parser = env.create_parser()
    opts   = parser.parse_args()
    conf = None
    with open(opts.configfn, 'r') as fd:
        conf = json.load(fd)

    # inside definitions of enviorment
    env.start(conf)
    
    # outside definitions of enviorment
    env.server_tracker = serverTracker.serverTracker()

    logfile = DIR_LOG + env.config.get('logfile', 'log.txt')
    loglevel = getattr(logging, env.config.get('loglevel', 'INFO'))
    logging.basicConfig(filename=logfile,
                        format='%(TIME)f %(filename)s:%(lineno)d/%(funcName)s %(message)s',
                        level=loglevel)
    logger = logging.getLogger()
    logger.addFilter(env.SimulationTimeFilter())
    logging.info('%s', json.dumps(env.config))
    
    print ('Test of distribuition:')
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
        if down_time > env.endtime:
            print(hid)
        ev = (env.now + down_time, server.Server.bootup, [hid, env.STATUS_NO_CHUNK, env.STATUS_STARTED])
        env.enqueue(ev)
    logging.info('created %d bootup events', len(env.evqueue))

    #assert (len(sim.evqueue) == (sim.config['maxhid'] // sim.host_tracker.vulnerable_period) + 1)

    while env.evqueue and env.now < env.endtime:
        _now, fn, data = env.dequeue()
        logging.debug('dequeue len %d', len(env.evqueue))
        fn(data)

    with open(filename_output, 'w') as fd:
        #hist.append(now, hid, status, STATUS_NO_CHUNK, count_chunking , count_no_chunk, count_complete, count_shutdown,count_fail)

        fd.write('TIME, ID, ST_B, ST_A, chunking, no_chunk, complete, shutdonw, fail, total\n')
        serves = np.zeros(env.maxid+1,dtype=np.int8)
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
                test = 1
            line += 1

    plotting_results()

    return 0

# COUNTER
def read_counter():
    return json.loads(open("counter.json", "r").read()) + 1 if path.exists("counter.json") else 0

def write_counter():
    with open("counter.json", "w") as f:
        f.write(json.dumps(counter))
counter = read_counter()
atexit.register(write_counter)


def plotting_results():


    info_array = np.array(env.hist)

    plt.plot(info_array[:,0], info_array[:,4]/env.maxid, label='Chunking'    , color='#000055', linestyle = '--')
    plt.plot(info_array[:,0], info_array[:,5]/env.maxid, label='No Chunk'    , color='#000075', linestyle = '--')
    plt.plot(info_array[:,0], info_array[:,6]/env.maxid, label='Complete'    , color='#000095', linestyle = '--')
    on_system = info_array[:,4] + info_array[:,5] + info_array[:,6]
    plt.plot(info_array[:,0], on_system/env.maxid, label='On'    , color='#0000FF')
    
    plt.plot(info_array[:,0], info_array[:,7]/env.maxid, label='Shutdown'    , color='r')
    plt.plot(info_array[:,0], info_array[:,8]/env.maxid, label='Fail'        , color='g')
    

    plt.xlabel('Time')
    plt.ylabel('proportion of')
    #plt.ylim((0.0,1.7))
    plt.legend(loc='right')
    filename_pdf ='exec_counter-{:>03d}.pdf'.format(counter)
    plt.savefig(_GRAPH_ + filename_pdf)
    #plt.show()
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