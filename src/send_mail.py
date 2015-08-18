# -*- coding: UTF-8 -*-
from email.header import Header
from email.mime.text import MIMEText

__author__ = 'xing'

import smtplib
import traceback


def send_mail(to_list, sub, message, cf):
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
