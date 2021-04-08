#!/usr/bin/env python3
# coding:utf-8
import base64
import time
import traceback

import requests

from instance.config import APIConfig
from nemo.common.utils.iputils import check_ip_or_domain
from nemo.common.utils.loggerutils import logger
from nemo.core.tasks.taskbase import TaskBase


class Fofa(TaskBase):
    '''调用fofa API接口进行资产收集
    支持ip与域名两种方式（注意：fofa里domain的话只能查询根域名，如baidu.com；IP只能是单个IP）
    参数:options
            {
                'target':   [ip/domain,ip/domain...]
                'org_id':   id,target关联的组织机构ID
            }
    任务结果:
        保存为ip或domain资产格式的列表：
        {'ip': '61.133.196.53', 'status': 'N/A', 'port': [{'port': '80', 'status': 'N/A', 'title': 'xxx', 'server': 'nginx/1.16.0'}]}
        {'domain': 'www.csg.cn', 'A': ['218.19.148.193']}
    '''

    def __init__(self):
        super().__init__()
        # FOFA的API KEY
        self.email = APIConfig.FOFA_EMAIL
        self.key = APIConfig.FOFA_KEY
        # FOFA地址
        self.base_url = 'https://fofa.so'
        self.search_api_url = '/api/v1/search/all'
        self.login_api_url = '/api/v1/info/my'
        # self.__get_userinfo()
        # 默认参数
        self.source = 'fofa'
        self.result_attr_keys = ('title', 'server')  # 要保存的属性字段

    def __get_userinfo(self):
        '''获取API KEY用户信息
        '''
        try:
            url = '{url}{api}'.format(
                url=self.base_url, api=self.login_api_url)
            data = {"email": self.email, 'key': self.key}
            req = requests.get(url, params=data)
            return req.json()
        except requests.exceptions.ConnectionError:
            error_msg = {"error": True, "errmsg": "Connect error"}
            logger.error(traceback.format_exc())
            logger.error(error_msg)

            return error_msg

    def __get_data(self, query_str='', page=1, fields='host,ip,port'):
        '''查询FOFA API，获取数据
        普通用户最多只能查询前100条记录；默认每页的size是100
        '''
        try:
            url = '{url}{api}'.format(
                url=self.base_url, api=self.search_api_url)
            query_str = bytes(query_str, 'utf-8')
            data = {'qbase64': base64.b64encode(query_str), 'email': self.email, 'key': self.key, 'page': page,
                    'fields': fields}
            req = requests.get(url, params=data, timeout=10)
            return req.json()
        except requests.exceptions.ConnectionError:
            error_msg = {"error": True, "errmsg": "Connect error"}
            logger.error(traceback.format_exc())
            logger.error(error_msg)

            return None

    def __fofa_search(self, query_str):
        '''查询FOFA
        '''
        data_ret = []
        # 查询前1000条记录（10页，每页100条记录）
        for i in range(1, 11):
            fofa_data = self.__get_data(
                query_str, i, 'host,ip,port,title,server,province,city,country_name')
            if fofa_data and 'results' in fofa_data and fofa_data['results']:
                data_ret.extend(fofa_data['results'])
            else:
                break
            time.sleep(1)

        return data_ret

    def __parse_ip_port(self, line):
        '''解析IP与PORT
        '''
        ip = line[1]
        # 只保留和解析ipv4地址
        if not check_ip_or_domain(ip):
            return None

        port = int(line[2])
        title = line[3]
        server = line[4]
        # location = ' '.join([line[5], line[6], line[7]])
        p = {'port': port}  # , 'status': 'N/A'}
        if title:
            p['title'] = title
        if server:
            p['server'] = server
        ip_port = {'ip': ip, 'port': [p, ]}  # 'status': 'N/A', }
        # if len(location) > 2:
        #     ip_port['location'] = location

        return ip_port

    def __parse_domain_ip(self, line):
        '''解析DOMAIN与IP
        '''
        host = line[0]
        ip = line[1]
        title = line[3]
        # 只保留和解析ipv4地址
        if not check_ip_or_domain(ip):
            return None

        data = host.replace(
            'https://', '').replace('http://', '').split(':')[0]
        # 去除IP
        if not check_ip_or_domain(data):
            domain = {'domain': data, 'A': [ip, ]}
            if title:
                domain['title'] = [title, ]
            return domain
        else:
            return None

    def prepare(self, options):
        '''解析参数
        '''
        self.target = []
        for t in options['target']:
            # if check_ip_or_domain(t):
            #     ip_target = parse_ip(t)
            #     if ip_target and isinstance(ip_target, (tuple, list)):
            #         self.target.extend(ip_target)
            #     else:
            #         self.target.append(ip_target)
            # else:
            self.target.append(t)
        self.org_id = self.get_option('org_id', options, self.org_id)

    def execute(self, target):
        '''查询FOFA
        '''
        ip_port = []
        domain_ip = []
        for t in target:
            # 查询FOFA
            if check_ip_or_domain(t):
                query_str = 'ip="{0}" || host="{0}" '.format(t)
            else:
                query_str = 'domain="{0}" || host="{0}" || cert="{0}"'.format(t)
            result = self.__fofa_search(query_str)
            # 解析结果
            for line in result:
                ipp = self.__parse_ip_port(line)
                if ipp:
                    ip_port.append(ipp)
                dip = self.__parse_domain_ip(line)
                if dip:
                    domain_ip.append(dip)

        return ip_port, domain_ip

    def run(self, options):
        '''执行任务
        '''
        self.prepare(options)
        # 查询API
        ip_port, domain_ip = self.execute(self.target)
        # 保存数据
        result = self.save_ip(ip_port)
        result.update(self.save_domain(domain_ip))
        result['status'] = 'success'

        return result
