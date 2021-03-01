#!/usr/bin/env python3
# coding:utf-8
from nemo.common.utils.iputils import check_ip_or_domain
from nemo.core.tasks.fingerprint.httpx import Httpx

from nemo.core.tasks.domain.ipdomain import IpDomain
from nemo.core.tasks.onlineapi.iplocation import IpLocation
from nemo.core.tasks.ipport.masscan import Masscan
from nemo.core.tasks.ipport.nmap import Nmap
from nemo.core.tasks.taskbase import TaskBase
from nemo.core.tasks.fingerprint.webtitle import WebTitle
from nemo.core.tasks.fingerprint.whatweb import WhatWeb


class PortScan(TaskBase):
    '''端口扫描综合任务
    参数：options
        {   
            'target':   [ip1,ip2,ip3...],ip列表（nmap格式）
            'port':     '1-65535'或者'--top-ports 1000',nmap能识别的端口格式
            'org_id':   id,target关联的组织机构ID
            'rate':     1000,扫描速率
            'ping':     True/False，是否PING
            'tech':     '-sT'/'-sS'/'-sV'，扫描技术
            'httpx':    True/False,是否调用httpx
            'iplocation':   True/False，是否调用iplocation
            'bin':      nmap/masscan，扫描方法
        }
    '''

    def __init__(self):
        super().__init__()
        # 任务名称
        self.task_name = 'portscan'
        # 任务描述
        self.task_description = '端口扫描综合任务'
        # 默认参数：
        self.source = 'portscan'
        self.result_attr_keys = ('service', 'banner', 'title', 'whatweb', 'server', 'httpx')
        self.whatweb = False
        self.iplocation = False
        self.httpx = False
        self.bin = 'masscan'

    def prepare(self, options):
        '''解析参数
        '''
        self.org_id = self.get_option('org_id', options, self.org_id)
        self.whatweb = self.get_option('whatweb', options, self.whatweb)
        self.httpx = self.get_option('httpx', options, self.httpx)
        self.iplocation = self.get_option('iplocation', options, self.iplocation)
        self.bin = self.get_option('bin', options, self.bin)
        # 将域名转换为IP
        target_ip = []
        ipdomain = IpDomain()
        for t in options['target']:
            host = t.strip()
            if check_ip_or_domain(host):
                target_ip.append(host)
            else:
                # 获取域名IP信息
                iplist = ipdomain.fetch_domain_ip(host)
                # 保存到数据库
                self.save_domain([iplist, ])
                # 如果没有CDN，则将ip地址加入到扫描目标地址
                if len(iplist['CNAME']) == 0 and len(iplist['A']) > 0:
                    target_ip.extend(iplist['A'])

        options['target'] = target_ip

    def run(self, options):
        '''执行端口扫描任务
        '''
        self.prepare(options)
        # 扫描
        if self.bin == 'nmap':
            scan_app = Nmap()
        else:
            scan_app = Masscan()
        scan_app.prepare(options)
        ip_ports = scan_app.execute()
        # iplocation:
        if self.iplocation:
            iplocation_app = IpLocation()
            iplocation_app.execute(ip_ports)
        # 是否调用whatweb
        if self.whatweb:
            whatweb_app = WhatWeb()
            whatweb_app.execute(ip_ports)
        # 是否调用httpx
        if self.httpx:
            httpx_app = Httpx()
            httpx_app.execute(ip_ports)
        # 保存数据
        result = self.save_ip(ip_ports)
        result['status'] = 'success'

        return result
