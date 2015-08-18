import ConfigParser
from util.mysql import MysqlDao

__author__ = 'xing'

import web

urls = ('/', 'Index',
        '/query/order', 'OrderQuery')
app = web.application(urls, globals())
render = web.template.render('template/', cache=False)


class Index:

    def GET(self):
        return render.index()


class OrderQuery:

    def GET(self):
        data = dict()
        data['act'] = mysql_db.select_useful_act()
        data['order'] = mysql_db.select_self_order_by_date()
        return render.query_order(data)

cf = ConfigParser.ConfigParser()
cf.read('web.conf')
mysql_db = MysqlDao(cf)

if __name__ == '__main__':
    app.run()