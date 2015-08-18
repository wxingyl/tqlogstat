# -*- coding: UTF-8 -*-
import web

__author__ = 'xing'

import time


class MysqlDao:
    def __init__(self, conf):
        which_db = 'local_db'
        self.db = web.database(dbn="mysql", host=conf.get(which_db, 'host'),
                               db=conf.get(which_db, 'name'), user=conf.get(which_db, 'user'),
                               pw=conf.get(which_db, 'passwd'), port=conf.getint(which_db, 'port'))

    def select_useful_act(self):
        now_timestamp = int(time.time())
        select_sql = 'select id, name from db_hd_activity where is_del = 0 and status = 1' \
                     ' and %d >= start_time and %d <= end_time and act_type = 1' % (now_timestamp, now_timestamp)
        return list(self.db.query(select_sql))

    def select_self_order_by_date(self, start_time = None, end_time = None):
        if not (start_time and end_time):
            end_time = int(time.time())
            start_time = time.localtime(end_time)
            start_time = end_time - start_time.tm_hour * 3600 - start_time.tm_min * 60 - start_time.tm_sec
        sql = 'select order_id, order_sn, user_id, sale_id, sale_name, order_status, add_time, attributes, ' \
              'order_flags, order_amount from db_order_info where add_time between %d and %d and attributes ' \
              'like "%%orderSource:SelfOrder%%"' % (start_time, end_time)
        return list(self.db.query(sql))
