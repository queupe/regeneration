#!/usr/bin/env python3


import numpy as np
import matplotlib.pyplot as plt
import csv
import sys
import json
import atexit
import subprocess

from datetime import datetime
from os import path

DIR_OUTPUT   = './output/'
DIR_GRAPH    = 'img/'
DIR_LATEX    = 'latex/'
DIR_TEMPLATE = 'template/'
OUTPUT_FILE  = 'servers'
OUTPUT_COUNT = 'counter'
OUTPUT_CONFG = 'config'
OUTPUT_LATEX = 'latex'

config = None

def read_repair_output(filename=DIR_OUTPUT+OUTPUT_FILE):

    with open(filename) as fd:
        lam = list(csv.reader(fd))
        arr = np.array(lam[1:], dtype=np.float)
    
    return arr

def read_repair_cost(filename=DIR_OUTPUT+OUTPUT_COUNT):

    with open(filename) as fd:
        lam = list(csv.reader(fd))
        arr = np.array(lam[1:], dtype=np.float)
    
    return arr

def save_parameters(config):
    global counter

    latex_info = DIR_TEMPLATE + 'template_1.tex'
    latex_out  = DIR_LATEX + OUTPUT_LATEX +'{:03d}.tex'.format(counter)

    with open(latex_info, 'r') as fdr:
        with open(latex_out, 'w') as fdw:
            i = 0
            for line in fdr:
                i += 1
                if i == 11:
                    fdw.write('\t\t\\textsf{{Sample {}}}'.format(counter))
                elif i == 28:
                    fdw.write('\t\t\t{:7.2f} \\\\ \n'.format(config['endtime']))
                elif i == 31:
                    fdw.write('\t\t\t{:d} \\\\ \n'.format(config['max_id']))
                elif i == 37:
                    fdw.write('\t\t\t{:s} \\\\ \n'.format(config['server']['fail_rate_distr']))
                elif i == 39:
                    fdw.write('\t\t\t{} \\\\ \n'.format(config['server']['fail_rate_param']))
                elif i == 42:
                    fdw.write('\t\t\t{:s} \\\\ \n'.format(config['server']['up_rate_distr']))
                elif i == 44:
                    fdw.write('\t\t\t{} \\\\ \n'.format(config['server']['up_rate_param']))
                elif i == 47:
                    fdw.write('\t\t\t{} \\\\ \n'.format(config['server']['shutdown_rate_distr']))
                elif i == 49:
                    fdw.write('\t\t\t{} \\\\ \n'.format(config['server']['shutdown_rate_param']))
                elif i == 55:
                    fdw.write('\t\t\t{:s} \\\\ \n'.format(config['repair']['class']))
                elif i == 58:
                    fdw.write('\t\t\t{:s} \\\\ \n'.format(config['repair']['activate_rate_distr']))
                elif i == 60:
                    fdw.write('\t\t\t{} \\\\ \n'.format(config['repair']['activate_rate_param']))
                elif i == 62:
                    fdw.write('\t\t\t{:7.3f} \\\\ \n'.format(config['repair']['activate_cost']))
                elif i == 65:
                    fdw.write('\t\t\t{:s} \\\\ \n'.format(config['repair']['activate_ctrl_rule']))
                elif i == 67:
                    fdw.write('\t\t\t{} \\\\ \n'.format(config['repair']['activate_ctrl_param']))
                elif i == 70:
                    fdw.write('\t\t\t{:s} \\\\ \n'.format(config['repair']['transfer_rate_distr']))
                elif i == 72:
                    fdw.write('\t\t\t{} \\\\ \n'.format(config['repair']['transfer_rate_param']))
                elif i == 74:
                    fdw.write('\t\t\t{:7.3f} \\\\ \n'.format(config['repair']['transfer_cost']))
                elif i == 80:
                    fdw.write('\t\t\t{:d} \\\\ \n'.format(config['chunk']['size']))
                elif i == 83:
                    fdw.write('\t\t\t{:d} \\\\ \n'.format(config['chunk']['recovery']))
                elif i == 86:
                    fdw.write('\t\t\t{:d} \\\\ \n'.format(config['chunk']['repair']))
                elif i == 89:
                    fdw.write('\t\t\t{:d} \\\\ \n'.format(config['chunk']['total']))
                elif i == 100:
                    filename_pdf ='exec_counter-{:>03d}.pdf'.format(counter)
                    fdw.write('\t\includegraphics {{img/{:s}}} \\\\ \n'.format(filename_pdf))

                else:
                    fdw.write(line)


# COUNTER
def read_counter():
    return json.loads(open("counter.json", "r").read()) if path.exists("counter.json") else 0

#def write_counter():
#    with open("counter.json", "w") as f:
#        f.write(json.dumps(counter))
counter = read_counter()
#atexit.register(write_counter)

def plotting_results():
    filename_cfg = '{}sample{:03d}_{}.json'.format(DIR_OUTPUT, counter, OUTPUT_CONFG)
    filename_out = '{}sample{:03d}_{}.csv'.format(DIR_OUTPUT, counter, OUTPUT_FILE)
    filename_cnt = '{}sample{:03d}_{}.csv'.format(DIR_OUTPUT, counter, OUTPUT_COUNT)

    #configfn = 'config/test_prime.json'
    with open(filename_cfg, 'r') as fd:
        config = json.load(fd)
    
    save_parameters(config)

    maxid = config['max_id']

    fig, ax = plt.subplots(nrows=2, ncols=1, sharex=True)
 
    info_array = read_repair_output(filename_out)
    cost_array = read_repair_output(filename_cnt)

    k = config['chunk']['recovery']/maxid
    Xk = np.array([info_array[0,0], info_array[-1,0]])
    Yk = np.array([k,k])
    ax[0].plot(Xk, Yk, color='#D3D3D3', linestyle = '--')
    #ax[0].text(Xk[0] - config['endtime']/50,Yk[0]-0.012,'k')

    d = config['chunk']['repair']/maxid
    Xd = np.array([info_array[0,0], info_array[-1,0]])
    Yd = np.array([d,d])
    ax[0].plot(Xd, Yd, color='#D3D3D3',  linestyle = '--')
    #ax[0].text(Xd[0] - config['endtime']/50,Yd[0]-0.01,'d')

    n = config['chunk']['total']/maxid
    Xn = np.array([info_array[0,0], info_array[-1,0]])
    Yn = np.array([n,n])
    ax[0].plot(Xn, Yn, color='#D3D3D3', linestyle = '--')
    #ax[0].text(Xn[0] - config['endtime']/50,Yn[0]-0.01,'n')


    ax[0].plot(info_array[:,0], info_array[:,4]/ maxid, linewidth=0.75, label='Chunking'    , color='#00BFFF', linestyle = '-')
    ax[0].plot(info_array[:,0], info_array[:,5]/ maxid, linewidth=0.75, label='No Chunk'    , color='#00FA94', linestyle = '-')
    ax[0].plot(info_array[:,0], info_array[:,6]/ maxid, linewidth=0.75, label='Complete'    , color='#0000FF', linestyle = '-')
    
    #plt.plot(range(100), np.ones(100))
    ax[0].plot(info_array[:,0], info_array[:,7]/ maxid, linewidth=0.5, label='Shutdown'    , color='r')
    ax[0].plot(info_array[:,0], info_array[:,8]/ maxid, linewidth=0.5, label='Fail'        , color='g')
    ax[0].legend(loc='upper right')
    ax[0].set_ylabel('proportion')

    lst_cost1 = list()
    lst_cost2 = list()
    cost1 = 0
    cost2 = 0
    time1 = 0
    time2 = 0
    for i in range(len(cost_array)):
        cost1b = cost_array[i,4] - cost1
        cost2b = cost_array[i,5] - cost2

        if cost1b > 0:
            time1b = cost_array[i,0] - time1
            if time1b > 0:
                time1 = time1b
                lst_cost1.append([cost_array[i,0], cost1b/time1])
                cost1 = cost_array[i,4]
                time1 = cost_array[i,0]
        if cost2b > 0:
            time2b = cost_array[i,0] - time2
            if time2b > 0:
                time2 = time2b
                lst_cost2.append([cost_array[i,0], cost2b/time2])
                cost2 = cost_array[i,5]
                time2 = cost_array[i,0]

    mtx_cost1 = np.array(lst_cost1)
    mtx_cost2 = np.array(lst_cost2)

    ax[1].semilogy(mtx_cost2[:,0], mtx_cost2[:,1], linewidth=0.5, label='Chunk cost/time', color='b')
    ax[1].semilogy(mtx_cost1[:,0], mtx_cost1[:,1], linewidth=0.5, label='Activation cost/time', color='r')
    ax[1].legend(loc='upper right')
    ax[1].set_ylabel('Cost')


    plt.xlabel('Time')
    #plt.ylabel('proportion of')
    #plt.ylim((0.0,1.7))
    
    filename_pdf ='exec_counter-{:>03d}.pdf'.format(counter)
    plt.savefig(DIR_LATEX + DIR_GRAPH + filename_pdf)
    #plt.show()
    plt.clf()

    latex_out  = OUTPUT_LATEX +'{:03d}.tex'.format(counter)
    with open('latex_name.txt','w') as fd:
        fd.write('{:s}'.format(latex_out))

def main():
    plotting_results()
    return 0

if __name__ == '__main__':
    #start = time.time()
    start_time = datetime.now()
    results = main()
    #end = time.time()
    time_elapsed = datetime.now() - start_time
    print("Time elapsed: {0}".format(time_elapsed))
    sys.exit(results)