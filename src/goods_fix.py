from __future__ import division
import json
from mysql import MysqlDao

__author__ = 'xing'


class GoodsFix:
    def __init__(self, cf):
        conf = dict()
        conf['host'] = cf.get('online_db', 'host')
        conf['user'] = cf.get('online_db', 'user')
        conf['passwd'] = cf.get('online_db', 'passwd')
        conf['name'] = cf.get('online_db', 'name')
        conf['port'] = cf.getint('online_db', 'port')
        conf['charset'] = cf.get('online_db', 'charset')
        self.shop_dao = MysqlDao(conf)

        conf['host'] = cf.get('online_db', 'sea_host')
        conf['user'] = cf.get('online_db', 'sea_user')
        conf['passwd'] = cf.get('online_db', 'sea_passwd')
        conf['name'] = cf.get('online_db', 'sea_name')
        conf['port'] = cf.getint('online_db', 'sea_port')
        conf['charset'] = cf.get('online_db', 'sea_charset')
        self.sea_dao = MysqlDao(conf)
        self.page_size = cf.getint('online_db', 'page_size')

    def seller_goods_fix(self):
        all_goods_id = self.shop_dao.select_goods_id_by_seller(2000)
        insert_goods_id = all_goods_id.difference(self.sea_dao.select_goods_rel(all_goods_id))
        goods_rel = []
        for e in self.shop_dao.select_goods_info(insert_goods_id):
            db_dict = dict()
            db_dict['seller_id'] = 2000
            db_dict['goods_id'] = e['goods_id']
            db_dict['goods_sn'] = e['new_goods_sn']
            db_dict['seller_goods_name'] = e['goods_name']
            db_dict['seller_goods_sn'] = e['attr_value']
            db_dict['seller_unit'] = e['measure_unit']
            db_dict['seller_valid'] = 1
            db_dict['status'] = 1
            db_dict['is_deleted'] = 'N'
            goods_rel.append(db_dict)
            if len(goods_rel) > self.page_size:
                self.sea_dao.insert_batch('sea_goods_rel', goods_rel)
                goods_rel = []
        if len(goods_rel) > 0:
            self.sea_dao.insert_batch('sea_goods_rel', goods_rel)
