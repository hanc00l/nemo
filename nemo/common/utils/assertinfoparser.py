#!/usr/bin/env python3
# coding:utf-8
from collections import defaultdict

from nemo.core.database.attr import DomainAttr, PortAttr
from nemo.core.database.colortag import IpColorTag, DomainColorTag
from nemo.core.database.domain import Domain
from nemo.core.database.ip import Ip
from nemo.core.database.memo import IpMemo, DomainMemo
from nemo.core.database.organization import Organization
from nemo.core.database.port import Port
from nemo.core.database.vulnerability import Vulnerability


class AssertInfoParser():
    '''资产信息（IP、域名）聚合
    '''

    def __init__(self):
        super().__init__()

    def __get_ip_domain(self, ip):
        '''查询IP关联的域名
        '''
        domain_set = set()
        domain_attrs_obj = DomainAttr().gets(query={'tag': 'A', 'content': ip})
        for domain_attr_obj in domain_attrs_obj:
            domain_obj = Domain().get(domain_attr_obj['r_id'])
            if domain_attr_obj:
                domain_set.add(domain_obj['domain'])

        return domain_set

    def get_ip_port_info(self, ip, ip_id):
        '''获取IP端口属性，并生成port、title、banner聚合信息
        '''
        port_list = []  # 端口列表
        port_status_dict = {}  # 端口对应的状态字典
        title_set = set()  # 标题聚合
        banner_set = set()  # banner聚合
        ports_attr_info = []  # 每一个端口的详细属性

        ports_obj = Port().gets(query={'ip_id': ip_id})
        for port_obj in ports_obj:
            port_list.append(port_obj['port'])
            if port_obj['status']:
                port_status_dict[str(port_obj['port'])] = port_obj['status']
            # 获取端口属性
            port_attrs_obj = PortAttr().gets(query={'r_id': port_obj['id']})
            FIRST_ROW = True
            # 每个端口的一个属性生成一行记录
            # 第一行记录显示IP和PORT，其它行保持为空（方便查看）
            for port_attr_obj in port_attrs_obj:
                pai = {}
                if FIRST_ROW:
                    pai.update(ip=ip, port=port_obj['port'])
                    FIRST_ROW = False
                else:
                    pai.update(ip='', port='')
                pai.update(id=port_attr_obj['id'], tag=port_attr_obj['tag'], content=port_attr_obj['content'],
                           source=port_attr_obj['source'],
                           update_datetime=port_attr_obj['update_datetime'].strftime('%Y-%m-%d %H:%M'))
                # 更新集合
                if port_attr_obj['tag'] == 'title':
                    title_set.add(port_attr_obj['content'])
                elif port_attr_obj['tag'] in ('banner', 'tag', 'server'):
                    if port_attr_obj['content'] and port_attr_obj['content'] != 'unknown':
                        banner_set.add(port_attr_obj['content'])

                ports_attr_info.append(pai)

        return port_list, title_set, banner_set, ports_attr_info, port_status_dict

    def get_ip_info(self, Id):
        '''聚合一个IP的详情
        '''
        ip_info = {}
        # 获取IP
        ip_obj = Ip().get(Id)
        if not ip_obj:
            return None
        ip_info.update(id=ip_obj['id'], ip=ip_obj['ip'], location=ip_obj['location'], status=ip_obj['status'],
                       create_datetime=ip_obj['create_datetime'].strftime(
                           '%Y-%m-%d %H:%M'), update_datetime=ip_obj['update_datetime'].strftime('%Y-%m-%d %H:%M'))
        # 获取组织名称
        if ip_obj['org_id']:
            organziation__obj = Organization().get(ip_obj['org_id'])
            if organziation__obj:
                ip_info.update(organization=organziation__obj['org_name'])
        else:
            ip_info.update(Organization='')
        # 端口、标题、banner、端口详情
        port_list, title_set, banner_set, ports_attr_info, port_status_dict = self.get_ip_port_info(
            ip_obj['ip'], ip_obj['id'])
        ip_info.update(port_attr=ports_attr_info)
        ip_info.update(title=list(title_set))
        ip_info.update(banner=list(banner_set))
        ip_info.update(port=port_list)
        # IP关联的域名
        domain_set = self.__get_ip_domain(ip_obj['ip'])
        ip_info.update(domain=list(domain_set))
        # 获取标记颜色：
        color_tag_obj = IpColorTag().get(ip_obj['id'])
        ip_info.update(
            color_tag=color_tag_obj['color'] if color_tag_obj else '')
        # 获取备忘录信息：
        memo_obj = IpMemo().get(ip_obj['id'])
        ip_info.update(memo=memo_obj['content'] if memo_obj else '')
        # 获取IP关联的漏洞信息：
        vul_results = Vulnerability().gets({'target': ip_obj['ip']})
        if vul_results and len(vul_results) > 0:
            vul_info = []
            for v in vul_results:
                vul_info.append(
                    {'id': v['id'], 'target': v['target'], 'url': v['url'], 'poc_file': v['poc_file'],
                     'source': v['source'],
                     'update_datetime': v['update_datetime'].strftime('%Y-%m-%d %H:%M')})
            ip_info.update(vulnerability=vul_info)
        else:
            ip_info.update(vulnerability=None)

        return ip_info

    def get_domain_info(self, Id):
        '''聚合一个DOMAIN的详情
        '''
        domain_info = {}
        # 获取DOMAIN
        domain_obj = Domain().get(Id)
        if not domain_obj:
            return None
        domain_info.update(id=domain_obj['id'],
                           domain=domain_obj['domain'],
                           create_datetime=domain_obj['create_datetime'].strftime('%Y-%m-%d %H:%M'),
                           update_datetime=domain_obj['update_datetime'].strftime('%Y-%m-%d %H:%M'))
        # 获取组织名称
        if domain_obj['org_id']:
            organziation__obj = Organization().get(domain_obj['org_id'])
            if organziation__obj:
                domain_info.update(organization=organziation__obj['org_name'])
        else:
            domain_info.update(organization='')
        domain_attrs_obj = DomainAttr().gets(query={'r_id': domain_obj['id']})
        # 获取域名的属性信息：title和ip,whatweb
        title_set = set()
        banner_set = set()
        ip_set = set()
        whatweb_set = set()
        httpx_set = set()
        for domain_attr_obj in domain_attrs_obj:
            if domain_attr_obj['tag'] == 'title':
                title_set.add(domain_attr_obj['content'])
            elif domain_attr_obj['tag'] == 'A':
                ip_set.add(domain_attr_obj['content'])
            elif domain_attr_obj['tag'] == 'whatweb':
                whatweb_set.add(domain_attr_obj['content'])
            elif domain_attr_obj['tag'] == 'server':
                banner_set.add(domain_attr_obj['content'])
            elif domain_attr_obj['tag'] == 'httpx':
                httpx_set.add(domain_attr_obj['content'])
        # 获取域名关联的IP端口详情：
        port_set = set()

        ip_port_list = []
        for domain_ip in ip_set:
            ip_obj = Ip().gets(query={'ip': domain_ip})
            if ip_obj and len(ip_obj) > 0:
                # port_list, title_set, banner_set, ports_attr_info
                p, t, b, pai, ps = self.get_ip_port_info(
                    ip_obj[0]['ip'], ip_obj[0]['id'])
                port_set.update(p)
                title_set.update(t)
                banner_set.update(b)
                ip_port_list.extend(pai)
        domain_info.update(ip=list(ip_set))
        domain_info.update(port=list(port_set))
        domain_info.update(title=list(title_set))
        domain_info.update(whatweb=list(whatweb_set))
        domain_info.update(httpx=list(httpx_set))
        domain_info.update(banner=list(banner_set))
        domain_info.update(port_attr=ip_port_list)
        # 获取标记颜色：
        color_tag_obj = DomainColorTag().get(domain_obj['id'])
        domain_info.update(
            color_tag=color_tag_obj['color'] if color_tag_obj else '')
        # 获取备忘录信息：
        memo_obj = DomainMemo().get(domain_obj['id'])
        domain_info.update(memo=memo_obj['content'] if memo_obj else '')
        # 获取关联的漏洞信息：
        vul_results = Vulnerability().gets({'target': domain_obj['domain']})
        if vul_results and len(vul_results) > 0:
            vul_info = []
            for v in vul_results:
                vul_info.append(
                    {'id': v['id'], 'target': v['target'], 'url': v['url'], 'poc_file': v['poc_file'],
                     'source': v['source'],
                     'update_datetime': v['update_datetime'].strftime('%Y-%m-%d %H:%M')})
            domain_info.update(vulnerability=vul_info)
        else:
            domain_info.update(vulnerability=None)

        return domain_info

    def statistics_ip(self, org_id=None, domain_address=None, ip_address=None, port=None, content=None, iplocation=None,
                      port_status=None, color_tag=None, memo_content=None, date_delta=None):
        '''根据查询条件，统计IP、IP的C段地址和相关的所有端口
        '''
        ip_table = Ip()
        port_table = Port()

        ip_list = []
        ip_port_list = []
        ip_c_set = set()
        port_set = set()
        location_dict = {}
        # 统计每个端口出现的次数
        port_count_dict = defaultdict(lambda: 0)
        ips = ip_table.gets_by_search(org_id=org_id, domain=domain_address, ip=ip_address, port=port, content=content,
                                      iplocation=iplocation, port_status=port_status, color_tag=color_tag,
                                      memo_content=memo_content, date_delta=date_delta, page=1, rows_per_page=100000)
        if ips:
            for ip_row in ips:
                # ip
                ip_list.append(ip_row['ip'])
                # C段
                ip_c = ip_row['ip'].split('.')[0:3]
                ip_c.append('0/24')
                ip_c_set.add('.'.join(ip_c))
                # location
                if ip_row['location']:
                    try:
                        location = (ip_row['location'].split(',')[0]).split(' ')[0].strip()
                        if location:
                            location_count = location_dict.get(location, 0)
                            location_dict[location] = location_count + 1
                    except:
                        pass
                # port
                ports_obj = port_table.gets(query={'ip_id': ip_row['id']})
                for port_obj in ports_obj:
                    port_set.add(port_obj['port'])
                    port_count_dict[str(port_obj['port'])] += 1
                    ip_port_list.append('{}:{}'.format(
                        ip_row['ip'], port_obj['port']))

        return ip_list, ip_c_set, port_set, port_count_dict, ip_port_list, location_dict

    def export_ip_memo(self, org_id=None, domain_address=None, ip_address=None, port=None, content=None,
                       iplocation=None, port_status=None, color_tag=None, memo_content=None, date_delta=None):
        '''导出ip相关的备忘录信息
        '''
        ip_table = Ip()
        memo_table = IpMemo()

        memo_list = []
        ips = ip_table.gets_by_search(org_id=org_id, domain=domain_address, ip=ip_address, port=port, content=content,
                                      iplocation=iplocation, port_status=port_status, color_tag=color_tag,
                                      memo_content=memo_content, date_delta=date_delta, page=1, rows_per_page=100000)
        if ips:
            for ip_row in ips:
                memo_obj = memo_table.get(ip_row['id'])
                if memo_obj:
                    memo_list.append('[+]{}'.format(ip_row['ip']))
                    memo_list.append(memo_obj['content'])
                    memo_list.append("")

        return memo_list

    def export_domain_memo(self, org_id=None, domain_address=None, ip_address=None, color_tag=None, memo_content=None,
                           date_delta=None):
        '''导出Domain相关的备忘录信息
        '''
        domain_table = Domain()
        memo_table = DomainMemo()

        memo_list = []
        domains = domain_table.gets_by_search(org_id, domain_address,
                                              ip_address, color_tag, memo_content, date_delta)
        if domains:
            for domain_row in domains:
                memo_obj = memo_table.get(domain_row['id'])
                if memo_obj:
                    memo_list.append('[+]{}'.format(domain_row['domain']))
                    memo_list.append(memo_obj['content'])
                    memo_list.append("")

        return memo_list
