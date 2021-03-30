#!/usr/bin/env python3
# coding:utf-8
import re
import traceback
from multiprocessing.dummy import Pool

import requests

from nemo.common.thirdparty.qqwry.qqwry import QQwry
from nemo.common.utils.iputils import check_ip_or_domain, parse_ip
from nemo.common.utils.loggerutils import logger
from nemo.common.utils.parseiplocation import IPLocationCustom
from nemo.core.database.ip import Ip
from nemo.core.tasks.domain.domainscan import IpDomain
from nemo.core.tasks.taskbase import TaskBase


class IpLocation(TaskBase):
    '''IP归属地查询
    参数：options
            {
                'target':['ip',...]#ip列表
            }
    任务结果：
        保存为ip或domain资产的格式
        [{'ip': '218.19.148.193', 'location': 'xxx'}, {'ip': '121.8.169.18', 'location': 'xxx'},
    '''

    def __init__(self):
        super().__init__()
        self.task_name = 'iplocation'
        self.task_description = 'ip 归属地查询'
        self.source = 'iplocation'

        self.headers = {
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)'}
        self.timeout = 5
        self.threads = 5

        self.iplocation_custom = None

    def __parse_hao7188com_data(self, text):
        '''解析hao7188com的返回数据信息
        '''
        ipinfo = []
        p1 = u'<span class="wz">(.*?)</span>'
        p2 = u'<img (.*?)/>'
        for p in [p1, ]:
            m = re.findall(p, text)
            if m:
                for x in m:
                    x = re.sub(p2, '', x)
                    ipinfo.append(x.strip())

        return ipinfo

    def __fetch_iplocation_from_7188_1(self, ip):
        '''调用www.hao7188.com的接口查询指定的IP地址
        '''
        url = 'http://www.hao7188.com/'
        session = requests.Session()
        try:
            r1 = session.get(url, headers=self.headers)
            if r1.status_code == requests.codes.ok:
                pattern = r'name="so_token" value="(.*?)">'
                m = re.findall(pattern, r1.text)
                token = m[0] if m and len(m) > 0 else ''
                if token != '':
                    url = 'http://www.hao7188.com/query.html?ip={}&so_token={}'.format(
                        ip, token)
                    r2 = session.get(url, headers=self.headers)
                    if r2.status_code == requests.codes.ok:
                        m = re.findall(
                            r"<script>window\.location\.href = '(.*?)'</script>", r2.text)
                        new_href = m[0] if m and len(m) > 0 else ''
                        if new_href != '':
                            url_new = 'http://www.hao7188.com/{}'.format(
                                new_href)
                            r3 = session.get(url_new, headers=self.headers)
                            return self.__parse_hao7188com_data(r3.text)
        except:
            logger.error(traceback.format_exc())
            logger.error('fetch ip location from 7188,ip:{}'.format(ip))

        return None

    def __fetch_iplocation_from_7188(self, ip):
        '''
        调用www.hao7188.com的接口查询指定的IP地址
        '''
        url = 'https://www.hao7188.com/ip/{}.html'.format(ip)
        session = requests.Session()
        r1 = session.get(url)
        if r1.status_code == requests.codes.ok:
            return self.__parse_hao7188com_data(r1.text)
        else:
            return []

    def __fetch_iplocation_from_ipcn(self, ip):
        '''调用ip.cn查询IP地址
        '''
        url = 'http://ip.cn?ip={}'.format(ip)

        try:
            r = requests.get(url, headers=self.headers, timeout=self.timeout)
            if r.status_code == requests.codes.ok:
                p = r'<code>(.*?)</code>'
                m = re.findall(p, r.text)
                return m
        except:
            logger.error(traceback.format_exc())
            logger.error('fetch ip location from ipcn,ip:{}'.format(ip))

        return None

    def __fetch_iplocation_from_qqwry(self, ip):
        try:
            q = QQwry()
            q.load_file('nemo/common/thirdparty/qqwry/qqwry_lastest.dat')
            result = q.lookup(ip)
            return result
        except:
            logger.error(traceback.format_exc())
            logger.error('fetch ip location from ipcn,ip:{}'.format(ip))

            return None

    def prepare(self, options):
        '''解析参数
        '''
        self.org_id = self.get_option('org_id', options, self.org_id)
        ipdomain = IpDomain()
        self.target = []
        for host in options['target']:
            if check_ip_or_domain(host):
                ip = parse_ip(host)
                if not ip:
                    continue
                if isinstance(ip, list):
                    for t in ip:
                        self.target.append({'ip': t})
                else:
                    self.target.append({'ip': ip})
            # 获取域名IP信息
            else:
                iplist = ipdomain.fetch_domain_ip(host)
                self.save_domain(([iplist, ]))
                # 如果没有CDN，则将ip地址加入到扫描目标地址
                if len(iplist['CNAME']) == 0 and len(iplist['A']) > 0:
                    for ip in iplist['A']:
                        self.target.append({'ip': ip})

    def __execute(self, ip):
        '''查询IP归属地
        '''
        if 'ip' not in ip:
            return
        # 查询自定义IP
        ip_loc = self.iplocation_custom.get_iplocation(ip['ip'])
        if ip_loc:
            ip['location'] = ip_loc
            return
        # 从第三方接口查询IP
        # ip_loc = self.__fetch_iplocation_from_7188(ip['ip'])
        # if ip_loc and len(ip_loc) > 0:
        #     ip['location'] = ','.join(ip_loc)
        #     return
        # ip_loc = self.__fetch_iplocation_from_ipcn(ip['ip'])
        # if ip_loc and len(ip_loc) >= 2:
        #     ip['location'] = ip_loc[1]
        # 从本地离线纯真数据库获取IP归属地
        ip_loc = self.__fetch_iplocation_from_qqwry(ip['ip'])
        if ip_loc:
            ip['location'] = ' '.join(ip_loc)

    def execute(self, target_list):
        '''执行任务
        '''
        # 自定义IP与位置
        self.iplocation_custom = IPLocationCustom()

        pool = Pool(self.threads)
        pool.map(self.__execute, target_list)
        pool.close()
        pool.join()

        return target_list

    def save(self, data):
        '''保存IP归属地结果到数据库
        只更新ip表的location字段
        '''
        ip_app = Ip()
        count = 0
        for ip in data:
            if 'location' in ip and ip['location']:
                if self.org_id:
                    ip['org_id'] = self.org_id
                count += 1 if ip_app.save_and_update(ip) > 0 else 0

        return count

    def run(self, options):
        '''根据IP获得归属地
        '''
        self.prepare(options)
        self.execute(self.target)
        result = {'status': 'success',
                  'count': self.save(self.target)}

        return result
