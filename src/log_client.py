# coding=utf-8
import json

__author__ = 'xing'


class LogStatClient(object):
    # name为统计的名称，key log文件中对应的关键字, key为list,默认同name
    def __init__(self, name, key=None):
        self.name = name
        if key:
            # 且关系
            self.key = key
        else:
            self.key = [name]
        self.result = 0

    # True:需要继续传递，需要下一个client继续处理
    # False: 无需传递，表示该cilent处理了该行log，无需传输给下一个client
    def on_change(self, line):
        is_match = True
        for k in self.key:
            if k not in line:
                is_match = False
                break
        if is_match:
            self.result += 1
            return False
        else:
            return True

    # 结果返回，list
    def get_result(self):
        return ["\t%s:\t%d 次" % (self.name, self.result)]


class OrderPayLogStat(LogStatClient):
    def __init__(self):
        super(OrderPayLogStat, self).__init__('订单支付信息回传超时')
        self.order_id = []

    def on_change(self, line):
        is_match = super(OrderPayLogStat, self).on_change(line)
        if not is_match:
            self.order_id.append(line[line.rfind('=')+1:].strip())
            return False
        else:
            return True

    def get_result(self):
        ret = super(OrderPayLogStat, self).get_result()
        ret.append('\t\t orderIds: %s' % (','.join(self.order_id)))
        return ret


class HttpLogStat(LogStatClient):
    def __init__(self):
        super(HttpLogStat, self).__init__('Http请求异常', ['请求出现异常', 'HttpUtil'])
        # 统计信息，key为Exception名称，value为list：index = 0 为次数; index = 1 为请求url统计，结构为dict(url, list())
        # 这儿list为url的调用时间集合
        self.stat = dict()

    def on_change(self, line):
        is_match = super(HttpLogStat, self).on_change(line)
        if not is_match:
            url = line[line.index('url:') + 5:]
            url = url[:url.rindex(',')]
            index = line.rfind(', ')
            if 'GET' in line:
                url += '\tGET'
            else:
                url += '\tPOST'
            if index > 0:
                key = line[index+2:]
                key = key[:key.index(': ')]
            else:
                key = 'Unknown Exception'
            if key not in self.stat:
                self.stat[key] = [0, dict()]
            self.stat[key][0] += 1
            if url not in self.stat[key][1]:
                self.stat[key][1][url] = list()
            self.stat[key][1][url].append(line[:line.index(']') + 1])
            return False
        return True

    def get_result(self):
        ret = super(HttpLogStat, self).get_result()
        for k, v in self.stat.items():
            ret.append('\t  %s:\t%d次调用' % (k, v[0]))
            ret.append('\t  请求的url:')
            for u, t in v[1].items():
                ret.append('\t\t' + u)
                ret.append('\t\t调用时间: ' + ', '.join(t))
        return ret


class ShopCrashLogStat(LogStatClient):
    def __init__(self):
        super(ShopCrashLogStat, self).__init__('Shop Java Crash', ['catch all exception', 'LogFilter'])
        self.crash_stat = dict()

    def on_change(self, line):
        if 'javax.servlet.ServletException' in line:
            start = line.index(':') + 1
            end = line.rfind('.')
            if start >= end or 'java.lang.' in line:
                end = len(line)
            key_str = line[start:end].strip()
            if key_str not in self.crash_stat:
                self.crash_stat[key_str] = 0
            self.crash_stat[key_str] += 1
            return False
        return super(ShopCrashLogStat, self).on_change(line)

    def get_result(self):
        ret = super(ShopCrashLogStat, self).get_result()
        for k, v in self.crash_stat.items():
            ret.append('\t\t%s:\t%d次调用' % (k, v))
        return ret


class StallCrashLogStat(LogStatClient):
    def __init__(self):
        super(StallCrashLogStat, self).__init__('Stall Java Crash', ['core.ResultServiceWrapper', '系统出错'])
        self.crash_stat = dict()
        self.have_crash = False

    def on_change(self, line):
        if self.have_crash:
            self.have_crash = False
            index = line.find(':')
            if index <= 0:
                return False
            key_str = line[:index].strip()
            if key_str not in self.crash_stat:
                self.crash_stat[key_str] = 0
            self.crash_stat[key_str] += 1
            return False
        if super(StallCrashLogStat, self).on_change(line):
            return True
        else:
            self.have_crash = True
            return False

    def get_result(self):
        ret = super(StallCrashLogStat, self).get_result()
        for k, v in self.crash_stat.items():
            ret.append('\t\t%s:\t%d次调用' % (k, v))
        return ret


class JPushLogStat(LogStatClient):
    def __init__(self, pre_file):
        super(JPushLogStat, self).__init__('JPush接口异常,推送失败', ['调用JPush接口发生异常'])
        self.jpush_stat = dict()
        self.pre_stat_file = pre_file

    def on_change(self, line):
        if 'cn.jpush.api.common.NativeHttpClient' in line:
            key_str = line[line.rindex('-') + 1:].strip()
            if key_str not in self.jpush_stat:
                self.jpush_stat[key_str] = 0
            self.jpush_stat[key_str] += 1
            return False
        return super(JPushLogStat, self).on_change(line)

    def get_result(self):
        ret = super(JPushLogStat, self).get_result()
        for k, v in self.jpush_stat.items():
            ret.append('\t\t%s:\t%d' % (k, v))
        alias = False
        stat_dict = dict()
        alias_id = list()
        for l in self.pre_stat_file.readlines():
            l = l.strip()
            if 'JPush stat start' == l:
                alias = True
            elif 'JPush stat end' == l:
                break
            elif alias:
                if 'call jpush api, DEBUG_EVN:' in l:
                    td = json.loads(l[l.index('{'):])
                    alias_id = td['audience']['alias']
                elif 'Got error response' in l:
                    td = json.loads(l[l.index('responseContent:') + len('responseContent:'):])
                    msg = td['error']['message']
                    if msg not in stat_dict:
                        stat_dict[msg] = [set(), 0]
                    stat_dict[msg][0].update(alias_id)
                    stat_dict[msg][1] += 1
        ret.append('\t  异常的具体信息如下: ')
        for k, v in stat_dict.items():
            ret.append('\t  %s，%d次调用, 销售id：%s' % (k, v[1], ','.join(v[0])))
        return ret
