# parse from log file like: 
# test_util.py(  354): INFO       : idx=13: sim=0.724 ttf=0.49 secs, time=4.14 secs, ntok=(782, 582) itok/sec=1586.07, otok/sec=159.71, otok/rtsec=140.68, response=<Response [200 OK]>, timeout=20.0
# get idx, sim, ttf, time, ntok, itok/sec, otok/sec, otok/rtsec

import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np

def get_metrics_from_log_file(log_file):
    with open(log_file, 'r') as f:
        for line in f:
            if 'INFO       : idx=' in line:
                print(f"Parsing line: {line.strip()}")
                idx = int(line.split('idx=')[1].split(':')[0])
                sim = float(line.split('sim=')[1].split(' ')[0])
                ttf = float(line.split('ttf=')[1].split(' ')[0]) * 1000 # convert to milliseconds
                time = float(line.split('time=')[1].split(' ')[0]) * 1000 # convert to milliseconds
                ntok_0 = int(line.split('ntok=')[1].split(' ')[0].strip('(),'))
                ntok_1 = int(line.split('ntok=')[1].split(' ')[1].strip('(),'))
                ntok = (ntok_0, ntok_1)
                itok_sec = float(line.split('itok/sec=')[1].split(' ')[0].strip('(),'))
                otok_sec = float(line.split('otok/sec=')[1].split(' ')[0].strip('(),'))
                otok_rtsec = float(line.split('otok/rtsec=')[1].split(' ')[0].strip('(),'))
                yield {
                    'idx': idx,
                    'sim': sim,
                    'ttf': ttf,
                    'time': time,
                    'ntok': ntok,
                    'itok_sec': itok_sec,
                    'otok_sec': otok_sec,
                    'otok_rtsec': otok_rtsec
                }

# add file path as argument, using argparse
import argparse

parser = argparse.ArgumentParser()
# log files are listed as empty separated string
parser.add_argument(
    '--log_files',
    nargs='+',
    help='Paths to the log files',
    default=['provider0.log', 'provider1.log', 'provider2.log'],
)
parser.add_argument(
    '--metric',
    help='Metric to plot',
    default='time',
)
parser.add_argument(
    '--output_file',
    help='Output file name',
    default='time_distribution.png',
)
parser.add_argument(
    '--x_label',
    help='X label',
    default='Percentile',
)
parser.add_argument(
    '--y_label',
    help='Y label',
    default='Time (ms)',
)
parser.add_argument(
    '--title',
    help='Title',
    default='Time distribution',
)

args = parser.parse_args()

log_files = args.log_files

all_providers_metrics = defaultdict()
for log_file in log_files:
    metrics = defaultdict(list)
    for metric in get_metrics_from_log_file(log_file):
        print(metric)
        metrics['ttf'].append(metric['ttf'])
        metrics['time'].append(metric['time'])
        metrics['otok_sec'].append(metric['otok_sec'])
        metrics['otok_rtsec'].append(metric['otok_rtsec'])
    log_file_name = log_file.split('/')[-1].split('.')[0]
    all_providers_metrics[log_file_name] = metrics

# plot all provider's time metric in same plot, x axis is percentile, y axis is time in milliseconds
for provider_name, metrics in all_providers_metrics.items():
    time_values = [np.percentile(metrics['time'], p) for p in range(0, 101, 5)]
    plt.plot([p for p in range(0, 101, 5)], time_values, label=provider_name)
    
plt.xlabel(args.x_label)
plt.ylabel(args.y_label)
plt.title(args.title)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
plt.savefig(args.output_file)

