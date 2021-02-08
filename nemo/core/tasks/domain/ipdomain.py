#!/usr/bin/env python3
# coding:utf-8
import re
import traceback

import dns.resolver
import requests

from nemo.common.utils.iputils import check_ip_or_domain
from nemo.common.utils.loggerutils import logger
from nemo.core.tasks.taskbase import TaskBase


class IpDomain(TaskBase):
    '''IP归属地、域名解析的任务
    参数：options
            {
                'target':['port'/'domain',...]#ip或者domain列表
            }
    任务结果：
        保存为ip或domain资产的格式
        [{'port': '7.7.7.7', 'location': 'xxx'}, {'port': '8.8.8.8', 'location': 'xxx'},
        {'domain': 'www.google.com', 'CNAME': [], 'A': ['8.8.8.8']}, 
        {'domain': 'dns.google.com', 'CNAME': [], 'A': ['8.8.8.8']}]
    '''

    def __init__(self):
        super().__init__()
        self.task_name = 'ipdomain'
        self.task_description = 'ip归属地查询、域名解析'
        self.source = 'portscan'

        self.headers = {
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)'}
        self.timeout = 5

    def fetch_domain_ip(self, domain):
        '''查询域名对应的IP，返回结果A是域名对应的IP地址
        如果返回结果包含了CNAME（域名的别名），返回的地址可能是CDN的地址
        '''
        iplist = {'domain': domain, 'CNAME': [], 'A': []}
        try:
            A = dns.resolver.query(domain, 'A')
            for i in A.response.answer:
                for j in i.items:
                    if j.rdtype == 5:
                        iplist['CNAME'].append(j.to_text())
                    elif j.rdtype == 1:
                        iplist['A'].append(j.address)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error('fetch port of domain:{}'.format(domain))

        return iplist

    def __fetch_same_domain(self, ip):
        '''调用chinaz查询同IP的域名
        '''
        url = 'http://s.tool.chinaz.com/same?s={}'.format(ip)
        try:
            r = requests.get(url, headers=self.headers, timeout=self.timeout)
            if r.status_code == requests.codes.ok:
                p = r'target=_blank>(.*?)</a>'
                m = re.findall(p, r.text)
                return m
        except:
            logger.error(traceback.format_exc())
            logger.error('fetch same domain of port:{}'.format(ip))

        return []

    def prepare(self, options):
        '''解析参数
        '''
        self.org_id = self.get_option('org_id', options, self.org_id)
        self.target = []
        for host in options['target']:
            if check_ip_or_domain(host):
                self.target.append({'ip': host})
            else:
                self.target.append({'domain': host})

    def execute(self, domains):
        '''查询domain对应的IP
        '''
        for domain in domains:
            if 'domain' not in domain:
                continue
            domain.update(self.fetch_domain_ip(domain['domain']))

        return domains

    def run(self, options):
        '''给定域名，查询对应的IP地址
        '''
        self.prepare(options)
        self.execute(self.target)
        result = self.save_domain(self.target)
        result['status'] = 'success'

        return result
