#!/bin/env python3
# -*- coding: utf-8 -*-

import psutil
import os
import time
import socket
import json
import redis


def get_ip_address():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return ip


class ProcessInfo(object):
    """
    process info
    """
    def __init__(self, process_name):
        self.__memory_limit_invalid_value = 9223372036854771712
        self.__cpu_shares_invalid_value = 2
        self.__monitor_rw_bytes = 0
        self.__static_info = {}
        pids = psutil.pids()
        for pid in pids:
            p = psutil.Process(pid)
            if process_name in p.name():
                self.process = psutil.Process(pid)
                self.__static_info['pid'] = pid
                self.__static_info['name'] = process_name
                break
        #得到静态信息
        if self.__static_info['pid'] == None:
            return
        self.__init_static_info__()


    def get_dynamic_info(self):
        dynamic = self.process.as_dict(attrs=['status', 'create_time', 'num_threads',
                'cpu_times', 'cpu_percent','cpu_num','memory_info','memory_percent','io_counters'])
        #memory_info
        memory_info = {}
        memory_info['rss'] = dynamic['memory_info'].rss
        memory_info['vms'] = dynamic['memory_info'].vms
        memory_info['shared'] = dynamic['memory_info'].shared
        memory_info['lib'] = dynamic['memory_info'].lib
        memory_info['data'] = dynamic['memory_info'].data
        memory_info['dirty'] = dynamic['memory_info'].dirty
        dynamic['memory_info'] = memory_info
        #cpu_times
        cpu_times = {}
        cpu_times['user'] = dynamic['cpu_times'].user
        cpu_times['system'] = dynamic['cpu_times'].system
        cpu_times['children_user'] = dynamic['cpu_times'].children_user
        cpu_times['children_system'] = dynamic['cpu_times'].children_system
        cpu_times['iowait'] = dynamic['cpu_times'].iowait
        dynamic['cpu_times'] = cpu_times
        # disk_io
        dynamic['disk_io'] = {}
        dynamic['disk_io']['read_bytes'] = dynamic['io_counters'].read_bytes
        dynamic['disk_io']['write_bytes'] = dynamic['io_counters'].write_bytes
        del dynamic['io_counters']
        # network_io
        dynamic['network_io'] = {}
        network = psutil.net_io_counters(pernic=True)
        if 'eth0' in network:
            dynamic['network_io']['bytes_sent'] = network['eth0'].bytes_sent
            dynamic['network_io']['bytes_recv'] = network['eth0'].bytes_recv
            dynamic['network_io']['dropin'] = network['eth0'].dropin
            dynamic['network_io']['dropout'] = network['eth0'].dropout
        else:
            dynamic['network_io']['bytes_sent'] = 0
            dynamic['network_io']['bytes_recv'] = 0
            dynamic['network_io']['dropin'] = 0
            dynamic['network_io']['dropout'] = 0
        return dynamic


    def get_static_info(self):
        return self.__static_info

    def __init_static_info__(self):
        """
        get process static info
        """
        self.__static_info['ip'] = get_ip_address()
        self.__static_info['total_memory'] = psutil.virtual_memory()[0]
        self.__static_info['total_cpu'] = psutil.cpu_count()
        memory_limit_file = '/proc/{}/root/sys/fs/cgroup/memory/memory.limit_in_bytes'.format(self.process.pid)
        cpu_shares_file = '/proc/{}/root/sys/fs/cgroup/cpu/cpu.shares'.format(self.process.pid)
        with open(memory_limit_file, 'r') as file:
            limit = int(file.read())
            if limit == self.__memory_limit_invalid_value:
                self.__static_info['memory_limit'] = None
            else:
                self.__static_info['memory_limit'] = limit

        with open(cpu_shares_file, 'r') as file:
            shares = int(file.read())
            if limit == self.__cpu_shares_invalid_value:
                self.__static_info['cpu_shares'] = None
            else:
                self.__static_info['cpu_shares'] = shares



if __name__ == "__main__":
    process_name = os.getenv('MONITOR_PROCESS_NAME')
    monitor_process = ProcessInfo(process_name)
    s = monitor_process.get_static_info()
    while(True):
        d = monitor_process.get_dynamic_info()
        dictMerged = dict(d, **s)
        timestamp = time.time()
        app_name = dictMerged['name'] + '-' + dictMerged['ip']
        process_info = {}
        process_info['app_name'] = dictMerged
        process_info['time'] = timestamp

        # redis_client = redis.Redis(host="10.105.128.193", port=6379, password = 'admin', decode_responses=True)
        redis_client = redis.Redis(host="redis-master", port=6379, password = 'admin', decode_responses=True)
        redis_client.set(app_name, json.dumps(process_info))
        time.sleep(3)
    # print(json.dumps(process_info))