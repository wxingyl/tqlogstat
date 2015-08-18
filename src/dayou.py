# -*- coding: UTF-8 -*-

import pymssql
import json

__author__ = 'xing'


class MSSQL:
    def __init__(self, conf):
        self.conn = pymssql.connect(host=conf['host'], user=conf['user'], password=conf['passwd'],
                                    database=conf['db'], charset=conf['charset'], port=conf['port'])
        self.cur = self.conn.cursor()

    def __del__(self):
        self.cur.close()
        self.conn.close()

    def exec_query(self, sql):
        self.cur.execute(sql)
        res_list = self.cur.fetchall()
        return res_list

    def exec_non_query(self, sql):
        self.cur.execute(sql)
        self.conn.commit()


class DayouStat:
    def __init__(self, cf):
        self.files = {'stock': '/Users/xing/Desktop/1001_goods_stock.json',
                      'price': '/Users/xing/Desktop/1001_goods_price.json'}
        conf = dict()
        conf['host'] = cf.get('dayou', 'host')
        conf['user'] = cf.get('dayou', 'user')
        conf['passwd'] = cf.get('dayou', 'passwd')
        conf['db'] = cf.get('dayou', 'db_name')
        conf['charset'] = cf.get('dayou', 'charset')
        conf['port'] = cf.getint('dayou', 'port')
        self.mssql = MSSQL(conf)
        self.file_name = '/Users/xing/Desktop/' + conf['db'] + '.result'

    def run(self):
        goods_sn_list = set()
        goods_dict = dict()
        stock_file = open(self.files['stock'], 'r')
        stock_data = json.loads(''.join(stock_file.readlines()))
        stock_file.close()
        stock_data = stock_data['data']
        for e in stock_data:
            goods_sn_list.add('\'%s\'' % e['attr_value'])
            goods_dict[e['attr_value']] = e['goods_id']
        price_file = open(self.files['price'], 'r')
        price_data = json.loads(''.join(price_file.readlines()))
        price_data = price_data['data']
        for e in price_data:
            goods_sn_list.add('\'%s\'' % e['attr_value'])
            goods_dict[e['attr_value']] = e['goods_id']
        sql_str = 'select fittingscoding, wareamount, price, lowprice, changetime from fit_fittingwareinfo where' \
                  ' fittingscoding in (' + ','.join(goods_sn_list) + ')'
        fit_ware = self.mssql.exec_query(sql_str)
        fit_price_dict = dict()
        for e in fit_ware:
            d = dict()
            d['num'] = e[1]
            d['price'] = e[2]
            d['changetime'] = e[4]
            fit_price_dict[e[0]] = d
        have_data = list()
        no_data = list()
        for e in stock_data:
            fit_code = e['attr_value']
            if fit_code in fit_price_dict:
                d = fit_price_dict.get(fit_code)
                have_data.append('\t goods_id: %d, %s' % (e['goods_id'], fit_code))
            else:
                no_data.append('\t goods_id: %d, %s' % (e['goods_id'], fit_code))
        result = list()
        result.append('未导入库存db_goods_stock商品分析[共%d]' % len(stock_data))
        result.append('在dayou的fit_fittingwareinfo中有记录')
        result.extend(have_data)
        result.append('共%d件商品' % len(have_data))
        have_data = []
        result.append('\n\n在dayou的fit_fittingwareinfo中找不到对应商品的记录')
        result.extend(no_data)
        result.append('共%d件商品' % len(no_data))
        no_data = []
        price_zero = list()
        for e in price_data:
            fit_code = e['attr_value']
            if fit_code in fit_price_dict:
                d = fit_price_dict.get(fit_code)
                if d['price'] > 0:
                    have_data.append('\t goods_id: %d, %s, num: %d, price: %f, changetime: %s'
                                     % (e['goods_id'], fit_code, d['num'], d['price'], str(d['changetime'])))
                else:
                    price_zero.append('\t goods_id: %d, %s' % (e['goods_id'], fit_code))
            else:
                no_data.append('\t goods_id: %d, %s' % (e['goods_id'], fit_code))
        result.append('\n\n\n未导入价格db_goods_warehouse商品分析[共%d]' % len(price_data))
        result.append('在dayou的fit_fittingwareinfo中有记录, 并且有报价[price > 0]')
        result.extend(have_data)
        result.append('共%d件商品' % len(have_data))
        result.append('\n\n在dayou的fit_fittingwareinfo中有记录，但是标价为0')
        result.extend(price_zero)
        result.append('共%d件商品' % len(price_zero))
        result.append('\n\n在dayou的fit_fittingwareinfo中找不到对应商品的记录')
        result.extend(no_data)
        result.append('共%d件商品' % len(no_data))
        result_file = open(self.file_name, 'w')
        i = 0
        for e in result:
            result[i] = e + '\n'
            i += 1
        result_file.writelines(result)
        result_file.close()
