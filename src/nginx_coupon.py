# -*- coding: UTF-8 -*-
from mysql import MysqlDao

__author__ = 'xing'


class NginxCoupon(object):
    def __init__(self, cf):
        self.act_id = cf.getint('coupon', 'act_id')
        self.page_size = cf.getint('online_db', 'page_size')
        self.date_period = [cf.getint('coupon', 'start_date'), cf.getint('coupon', 'end_date')]
        conf = dict()
        conf['host'] = cf.get('online_db', 'host')
        conf['user'] = cf.get('online_db', 'user')
        conf['passwd'] = cf.get('online_db', 'passwd')
        conf['name'] = cf.get('online_db', 'name')
        conf['port'] = cf.getint('online_db', 'port')
        conf['charset'] = cf.get('online_db', 'charset')
        self.dao = MysqlDao(conf)
        self.hits_conf = dict()
        self.hits_conf[30] = cf.getfloat('coupon', 'hits_30')
        self.hits_conf[50] = cf.getfloat('coupon', 'hits_50')
        self.hits_conf[100] = cf.getfloat('coupon', 'hits_100')
        self.hits_conf[300] = cf.getfloat('coupon', 'hits_300')
        self.hits_conf[500] = cf.getfloat('coupon', 'hits_500')

    def run(self):
        start = 0
        user_hits = self.dao.select_hits_by_actid(self.act_id, start, self.page_size)
        unique_key = ['user_id', 'act_id']
        hits_key = self.hits_conf.keys()
        hits_key.sort()
        user_totle = 0
        while user_hits:
            user_totle += len(user_hits)
            for e in user_hits:
                if e['hits'] < hits_key[0]:
                    continue
                db_dict = dict()
                db_dict['user_id'] = e['user_id']
                db_dict['act_id'] = self.act_id
                db_dict['effective_date'] = self.date_period[0]
                db_dict['expiry_date'] = self.date_period[1]
                db_dict['status'] = 0
                db_dict['is_deleted'] = 'N'
                index = -1
                for k in hits_key[::-1]:
                    if e['hits'] >= k:
                        break
                    index -= 1
                db_dict['face_value'] = self.hits_conf[hits_key[index]]
                self.dao.insert_or_update_template('db_hd_coupon', db_dict, unique_key)
            start += self.page_size
            user_hits = self.dao.select_hits_by_actid(self.act_id, start, self.page_size)
        print '插入用户优惠劵条目: %d 张' % user_totle
