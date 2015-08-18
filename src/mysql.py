# -*- coding: UTF-8 -*-
__author__ = 'xing'

import MySQLdb
import MySQLdb.cursors
import datetime


class PDBC:
    def __init__(self, conf):
        self.conn = MySQLdb.connect(host=conf['host'], user=conf['user'], passwd=conf['passwd'], db=conf['name'],
                                    port=conf['port'], charset=conf['charset'], cursorclass=MySQLdb.cursors.DictCursor)
        self.cur = self.conn.cursor()

    def __del__(self):
        self.cur.close()
        self.conn.close()

    def get_data(self, sql):
        self.cur.execute(sql)
        result = self.cur.fetchall()
        return result

    def exec_data(self, sql):
        result = self.cur.execute(sql)
        self.conn.commit()
        return result

    # 插入函数，返回最后插入的主键id
    def insert_data(self, sql):
        self.cur.execute(sql)
        new_id = int(self.cur.lastrowid)
        self.conn.commit()
        return new_id


class MysqlDao:
    def __init__(self, conf):
        self.db = PDBC(conf)

    def insert_batch(self, table, dic_list):
        gmt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for e in dic_list:
            e['gmt_create'] = gmt
            e['gmt_modified'] = gmt
            e['creator'] = 10
            e['modifier'] = 10
        sql = 'insert into ' + table + ' ( ' + ', '.join(dic_list[0].keys()) + ' ) values '
        value_list = list()
        for e in dic_list:
            vl = list()
            for v in e.values():
                vl.append("'" + str(v) + "'")
            value_list.append('( ' + ', '.join(vl) + ' )')
        sql += ','.join(value_list)
        return self.db.insert_data(sql)

    def insert_temple(self, table, dic):
        gmt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dic['gmt_create'] = gmt
        dic['gmt_modified'] = gmt
        sql = 'insert into ' + table + '(' + ', '.join(dic.keys()) + ') values'
        value_list = list()
        for value in dic.values():
            value_list.append('"' + str(value) + '"')
        sql += '(' + ','.join(value_list) + ')'
        return self.db.insert_data(sql)

    def insert_or_update_template(self, table, db_dict, unique_key, primary_name='id'):
        select_sql = str()
        for key in unique_key:
            select_sql += key + ' = "' + str(db_dict[key]) + '" and '
        primary_key_id = 0
        if select_sql:
            select_sql = 'select id from %s where %s' % (table, select_sql[:-5])
            data = self.db.get_data(select_sql)
            if data:
                primary_key_id = data[0][primary_name]
        if primary_key_id > 0:
            gmt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db_dict['gmt_modified'] = gmt
            value_list = list()
            for key, value in db_dict.items():
                value_list.append('%s = "%s"' % (key, str(value)))
            self.db.exec_data('update %s set %s %s' % (
            table, ','.join(value_list), ' where %s = %d' % (primary_name, primary_key_id)))
        else:
            primary_key_id = self.insert_temple(table, db_dict)
        return primary_key_id

    def select_order_goods_by_order_id(self, order_ids):
        str_list = list()
        for e in order_ids:
            str_list.append(str(e))
        select_sql = 'select rec_id, order_id, goods_id, goods_number, sold_price, conversion_value' \
                     ' from db_order_goods where order_id in ( ' + ",".join(str_list) + ")"
        return self.db.get_data(select_sql)

    def update_order_goods_sold_price(self, db_dict, rec_id):
        db_dict['gmt_modified'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        value_list = list()
        for key, value in db_dict.items():
            value_list.append('%s = "%s"' % (key, str(value)))
        self.db.exec_data('update db_order_goods set %s where %s' % (','.join(value_list), 'rec_id = %d' % rec_id))

    def update_sync_order_goods_sold_price(self, db_dict, rec_id):
        value_list = list()
        for key, value in db_dict.items():
            value_list.append('%s = "%s"' % (key, str(value)))
        self.db.exec_data('update db_sync_order_goods set %s where %s' % (','.join(value_list), 'rec_id = %d' % rec_id))

    def select_hits_by_actid(self, act_id, start, page):
        select_sql = 'select user_id, hits from db_hd_share_hits where is_deleted = "N"' \
                     ' and act_id = %d limit %d, %d' % (act_id, start, page)
        return self.db.get_data(select_sql)

    # return set
    def select_goods_id_by_seller(self, seller_id):
        select_sql = 'select goods_id from db_goods where seller_id = %d' % (seller_id)
        ret = set()
        for e in self.db.get_data(select_sql):
            ret.add(e['goods_id'])
        return ret

    def select_goods_info(self, ids):
        str_list = list()
        for e in ids:
            str_list.append(str(e))
        select_sql = 'select a.goods_id, b.new_goods_sn, b.goods_name, b.measure_unit, a.attr_value from db_goods_attribute a ' \
                     'left join db_goods b on a.goods_id = b.goods_id where a.attr_id = 570 and b.goods_id in (%s)' % (','.join(str_list))
        return self.db.get_data(select_sql)

    # return set
    def select_goods_rel(self, ids):
        str_list = list()
        for e in ids:
            str_list.append(str(e))
        select_sql = 'select goods_id from sea_goods_rel where goods_id IN (%s)' % (','.join(str_list))
        ret = set()
        for e in self.db.get_data(select_sql):
            ret.add(e['goods_id'])
        return ret