# -*- coding: UTF-8 -*-
import traceback
import urllib
import time
from mysql import MysqlDao
from send_mail import send_mail

__author__ = 'xing'

import datetime


class NginxClient(object):
    def __init__(self, debug, cf):
        self.debug = debug
        self.cf = cf

    def change(self, nginx):
        return True

    def stat_result(self):
        pass


class ShareNginxClient(NginxClient):
    def __init__(self, debug, cf):
        super(ShareNginxClient, self).__init__(debug, cf)
        self.user_hits = dict()
        self.user_ip = dict()
        self.act_id = cf.getint('hits', 'act_id')
        self.match_url = ['activity/tuesday/index.html?', 'actId=' + str(self.act_id), 'uid=']
        self.region_time = [cf.getint('hits', 'start_time'), cf.getint('hits', 'end_time')]

    def change(self, nginx):
        for m in self.match_url:
            if m not in nginx['request'][1]:
                return True
        if nginx['timestamp'] < self.region_time[0] or nginx['timestamp'] > self.region_time[1]:
            return False
        request_url = nginx['request'][1]
        request_url = request_url[request_url.index('uid=') + 4:]
        index = request_url.find('&')
        if index == -1:
            index = len(request_url)
        uid = request_url[:index]
        if uid == '0' or not uid.isdigit():
            return False
        if uid not in self.user_hits:
            self.user_hits[uid] = 0
            self.user_ip[uid] = set()
        if nginx['remote_addr'] not in self.user_ip[uid]:
            self.user_ip[uid].add(nginx['remote_addr'])
            self.user_hits[uid] += 1
        return False

    def stat_result(self):
        conf = dict()
        conf['host'] = self.cf.get('online_db', 'host')
        conf['user'] = self.cf.get('online_db', 'user')
        conf['passwd'] = self.cf.get('online_db', 'passwd')
        conf['name'] = self.cf.get('online_db', 'name')
        conf['charset'] = self.cf.get('online_db', 'charset')
        conf['port'] = self.cf.getint('online_db', 'port')
        dao = MysqlDao(conf)
        unique_key = ['user_id', 'act_id']
        for user_id, hits in self.user_hits.items():
            db_dict = dict()
            db_dict['user_id'] = user_id
            db_dict['act_id'] = self.act_id
            db_dict['hits'] = hits
            db_dict['is_deleted'] = 'N'
            dao.insert_or_update_template('db_hd_share_hits', db_dict, unique_key)
        print '统计nginx log得到%d位用户的点击量' % len(self.user_hits)


class YuanXiaoClient(NginxClient):
    def __init__(self, debug, cf):
        super(YuanXiaoClient, self).__init__(debug, cf)
        self.end_time = cf.getint('yuanxiao', 'end_time')
        self.start_time = cf.getint('yuanxiao', 'start_time')
        self.pv_activity = 0
        self.pv_user = set()
        self.participate_user = set()

    def get_uid(self, url_str):
        url_str = url_str[url_str.index('?'):]
        for s in url_str.split('&'):
            if 'uid' in s:
                return int(s[4:])
        return 0

    def change(self, nginx):
        if self.end_time < nginx['timestamp'] < self.start_time:
            return False
        request_url = nginx['request'][1]
        if 'activity/yuanxiao/index.html?actId=270' in request_url:
            self.pv_activity += 1
        elif '/lottery/tangyuan_home' in request_url:
            self.pv_user.add(self.get_uid(request_url))
        elif '/lottery/draw_lottery' in request_url:
            self.participate_user.add(self.get_uid(request_url))
        else:
            return True
        return False

    def stat_result(self):
        message = list()
        message.append('Hi All:')
        message.append('  3月5日汤圆活动用户行为数据统计如下：')
        message.append('\t活动页面访问量: %d' % self.pv_activity)
        message.append('\t活动页面访问人数: %d' % len(self.pv_user))
        message.append('\t活动页面游戏参与人数: %d' % len(self.participate_user))
        message.extend(['\n', '   thanks!', 'xingxing.wang'])
        mailto_list = ['xingxing.wang@tqmall.com']
        send_mail(mailto_list, '3月5日汤圆活动用户行为数据统计', '\n'.join(message), self.cf)


class NginxServer(object):
    def __init__(self, source_file, cf):
        self.source_file = source_file
        self.client = list()
        self.act_id = cf.getint('hits', 'act_id')

    def register(self, client):
        if isinstance(client, NginxClient):
            self.client.append(client)
        else:
            raise ValueError, 'must be Client object'

    def unregister(self, client):
        if isinstance(client, NginxClient):
            self.client.remove(client)

    def clear_register(self):
        self.client = list()

    def run(self):
        for line in self.source_file.readlines():
            line = line.strip()
            if not line:
                continue
            nginx = dict()
            try:
                tmp_index = line.index(' "')
                li = line[:tmp_index].split(' ')
                nginx['remote_addr'] = li[0]
                nginx['timestamp'] = datetime.datetime.strptime(li[3][1:], '%d/%b/%Y:%H:%M:%S')
                nginx['timestamp'] = time.mktime(nginx['timestamp'].timetuple())
                line = line[tmp_index + 2:]
                tmp_index = line.index('" ')
                nginx['request'] = line[:tmp_index].split(' ')
                if len(nginx['request']) < 2:
                    continue
                nginx['request'][1] = urllib.unquote(nginx['request'][1])

                line = line[tmp_index + 2:]
                tmp_index = line.index(' "')
                li = line[:tmp_index].split(' ')
                nginx['status'] = int(li[0])
                nginx['body_bytes_sent'] = int(li[1])

                line = line[tmp_index + 2:]
                tmp_index = line.index('"')
                nginx['http_referer'] = line[:tmp_index]
                if nginx['http_referer'] == '-':
                    nginx['http_referer'] = None
                else:
                    nginx['http_referer'] = urllib.unquote(nginx['http_referer'])

                line = line[tmp_index + 3:]
                tmp_index = line.index('"')
                nginx['http_user_agent'] = line[:tmp_index]
            except Exception:
                print 'nginx log存在异常 line: ' + line + ',' + traceback.format_exc()
                continue
            for call in self.client:
                if not call.change(nginx):
                    continue

    def result(self):
        for call in self.client:
            call.stat_result()
