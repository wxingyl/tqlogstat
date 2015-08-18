# -*- coding: UTF-8 -*-
import ConfigParser
import smtplib
import traceback
import sys
import time
import json
import argparse

from log_client import LogStatClient, HttpLogStat, ShopCrashLogStat, StallCrashLogStat, OrderPayLogStat
from log_server import LogStatServer

# from dayou import DayouStat
# from nginx_stat import NginxServer, YuanXiaoClient
# from goods_fix import GoodsFix

reload(sys)
sys.setdefaultencoding('utf-8')
from email.header import Header
from email.mime.text import MIMEText

__author__ = 'xing'


def send_mail(to_list, sub, message):
    me = "%s<%s>" % (Header(cf.get('mail', 'name'), 'utf-8'), cf.get('mail', 'user'))
    msg = MIMEText(message, _charset='utf-8')
    msg['Subject'] = Header(sub, 'utf-8')  # 设置主题
    msg['From'] = me
    msg['To'] = ";".join(to_list)
    try:
        s = smtplib.SMTP()
        s.connect(cf.get('mail', 'host'))
        s.login(cf.get('mail', 'user'), cf.get('mail', 'passwd'))
        s.sendmail(me, to_list, msg.as_string())
        s.close()
        return True
    except Exception:
        print '发送邮件失败：' + traceback.format_exc()
        return False


def send_warn(message):
    message = 'python程序调用：\n %s\n    thanks!\n xingxing.wang' % message
    mailto_list = cf.get('mail', 'warn_mail_to_list').split(',')
    send_mail(mailto_list, 'log分析异常', message)


def send_report_email(source_file, pre_file, date_str, debug):
    stat_server = LogStatServer(source_file)
    stat_server.register(LogStatClient('城市站选择错误'))
    stat_server.register(LogStatClient('版本判断失败,默认为最新版', ['版本判断失败']))
    stat_server.register(LogStatClient('crm订单回写数据返回报错', ['crm 订单回写 数据返回报错']))
    stat_server.register(LogStatClient('销售代下单,创建订单失败', ['销售代下单', '创建订单失败']))
    stat_server.register(LogStatClient('短信发送错误', ['短信发送错误:action', 'SendSmsThread']))
    stat_server.register(LogStatClient('json反序列化失败', ['反序列化json失败']))
    stat_server.register(LogStatClient('通过百度地图获取城市坐标失败', ['BaiduMapUtil', '通过百度地图获取城市坐标失败']))
    stat_server.register(OrderPayLogStat())
    stat_server.register(StallCrashLogStat())
    stat_server.register(ShopCrashLogStat())
    stat_server.register(HttpLogStat())
    # stat_server.register(JPushLogStat(pre_file))
    stat_server.run()
    message = list()
    message.append('Hi All:')
    message.append('  iServer %s 运行log统计分析结果如下：' % date_str)
    message.extend(stat_server.stat_result())
    message.extend(['\n', '   thanks!', 'xingxing.wang'])
    stat_server.clear_register()
    if debug:
        mailto_list = cf.get('mail', 'debug_mailto_list').split(',')
    else:
        mailto_list = cf.get('stat', 'mailto_list').split(',')
    if not send_mail(mailto_list, 'iServer %s 运行log统计分析' % date_str, '\n'.join(message)):
        send_warn('\n'.join(message))


def high_quality_user(source_file, debug):
    if debug:
        mailto_list = cf.get('mail', 'debug_mailto_list').split(',')
    else:
        mailto_list = cf.get('high_user', 'mailto_list').split(',')
    user_obj = json.loads(source_file.readlines()[1])['data']
    sub = time.strftime('%H:%M', time.localtime(time.time())) + '分优质客户交集'
    text_list = ['Hi All:', '  %s:' % sub]
    tmp_text = []
    if user_obj:
        for k, v in user_obj.items():
            tmp_text.append('\n%s: %s' % (k, str(user_obj[k])))
    else:
        tmp_text.append('\t优质客户目前为空')
    text_list.extend(sorted(tmp_text))
    text_list.append('\n   thanks!')
    text_list.append('xingxing.wang')
    send_mail(mailto_list, sub, '\n'.join(text_list))


# def nginx_stat(source_file, debug):
#     server = NginxServer(source_file, cf)
#     # server.register(ShareNginxClient(debug, cf))
#     server.register(YuanXiaoClient(debug, cf))
#     server.run()
#     server.result()


def nginx_coupon(debug):
    # coupon = NginxCoupon(cf)
    #   coupon.run()
    pass


def goods_fix():
    pass
    # GoodsFix(cf).seller_goods_fix()


def main(action, debug, source_file, stat_date=None, ext_file=None):
    if action == 'stat':
        send_report_email(source_file, ext_file, stat_date, debug)
    elif action == 'user':
        high_quality_user(source_file, debug)
    elif action == 'nginx':
        pass
        # nginx_stat(source_file, debug)
    elif action == 'coupon':
        nginx_coupon(debug)
    elif action == 'dayou':
        pass
        # dayou = DayouStat(cf)
        # dayou.run()
    elif action == 'goods_fix':
        goods_fix()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage="tqmall iServer log analysis and statistics")
    parser.add_argument('-a', help="执行分析统计的类型", choices=['user',
                        'stat', 'nginx', 'coupon', 'dayou', 'goods_fix'],
                        required=True, dest='action')
    parser.add_argument('-f', help="统计的log文件", dest='file', type=file)
    parser.add_argument('-ef', help="统计的log文件", dest='ext_file', type=file)
    parser.add_argument('-d', help="debug模式", action='store_true', dest='debug')
    parser.add_argument('-t', help="stat日常log统计的执行时间", dest='time')
    parser.add_argument('-c', help="运行的配置文件", dest='config', required=True)
    args = parser.parse_args()
    global cf
    cf = ConfigParser.ConfigParser()
    cf.read(args.config)
    main(args.action, args.debug, args.file, stat_date=args.time, ext_file=args.ext_file)
