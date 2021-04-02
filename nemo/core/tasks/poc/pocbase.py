#!/usr/bin/env python3
# coding:utf-8
import json
import os
import traceback
from urllib.parse import urlparse

from nemo.common.utils.loggerutils import logger
from nemo.core.database.vulnerability import Vulnerability
from nemo.core.tasks.taskbase import TaskBase


class PocBase(TaskBase):
    '''调用POC执行验漏洞验证的基础类
    参数:options
            {   
                'target':   [ip1,ip2,ip3...],ip或domain列表）
                'poc_file': 调用的poc文件
            }
    任务结果:
        保存为vulnerability格式的列表：
        [{'target':1.2.3.4,'url':'127.0.0.1:7001','poc_file':'weblogic_console_all.py','source':'pocsuit3','extra':'xxx'},...]
    '''

    def __init__(self):
        super().__init__()

        # 任务名称
        self.task_name = 'pocbase'
        # 任务描述
        self.task_description = '调用POC进行漏洞验证'
        # 参数
        self.source = 'pocbase'
        self.POC_PATH = ''
        self.POC_FILE_EXT = ''
        # 默认的参数
        self.target = []
        self.poc_file = ''

    def __parse_xray_json_file(self, json_data):
        if not json_data:
            return []

        vul_results = []
        for data in json.loads(json_data):
            vul = {'poc_file': self.poc_file,
                   'source': 'xray', 'url': data['target']['url']}
            pr = urlparse(vul['url'])
            vul.update(target=pr.hostname)
            if 'detail' in data and 'snapshot' in data['detail']:
                if len(str(data['detail']['snapshot'])) > 2000:
                    vul['extra'] = str(data['detail']['snapshot'])[:2000] + '...'
                else:
                    vul['extra'] = str(data['detail']['snapshot'])

            vul_results.append(vul)

        return vul_results

    def execute_verify(self):
        '''调用验证漏洞
        由继承子类实现
        '''

    def prepare(self, options):
        '''解析参数
        '''
        self.target = options['target']
        self.poc_file = options['poc_file']

    def check_poc_exist(self, poc_file):
        '''检查POC文件存在
        '''
        full_path_poc_file = os.path.join(self.POC_PATH, poc_file)
        if os.path.exists(full_path_poc_file) and os.path.isfile(full_path_poc_file):
            return True

        return False

    def load_poc_files(self):
        '''获取poc文件列表
        '''
        poc_files = []
        try:
            for name in os.listdir(self.POC_PATH):
                if os.path.isfile(os.path.join(self.POC_PATH, name)) and os.path.splitext(name)[-1] == self.POC_FILE_EXT:
                    poc_files.append(name)
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error('load {} poc files fail:{}'.format(self.POC_PATH, str(e)))

        return sorted(poc_files)

    def execute(self):
        '''执行任务
        '''
        vul_results = []
        try:
            vul_results.extend(self.execute_verify())
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error('{} verify target:{}'.format(self.source, self.target))

        return vul_results

    def run(self, options):
        '''执行POC验证任务
        '''
        try:
            self.prepare(options)
            vul_results = self.execute()

            result = {'status': 'success', 'vulnerability': 0}
            vul_app = Vulnerability()
            for v in vul_results:
                if vul_app.save_and_update(v):
                    result['vulnerability'] += 1

            return result
        except Exception as e:
            logger.error(traceback.format_exc())
            return {'status': 'fail', 'msg': str(e)}
