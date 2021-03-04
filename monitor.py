#!/bin/env python3
# -*- coding: utf-8 -*-

import psutil
import os
import time

def process_list():
    process_name = os.getenv('MONITOR_PROCESS_NAME')
    pids = psutil.pids()
    for pid in pids:
        p = psutil.Process(pid)
        if process_name in p.name():
            print("pid-%d,  pname-%s" % (pid, p.name()))
            print(p.status())
            print(p.num_ctx_switches())
            print(p.num_threads())
            print(p.create_time())
            print(p.io_counters())
            print(p.memory_info())
            print(p.memory_percent())


if __name__ == "__main__":
    while(True):
        process_list()
        time.sleep(5)