# -*- coding: utf-8 -*-

import os

__author__ = 'xing'


class PathNode:
    def __init__(self, class_name, super_path):
        self.class_name = class_name
        self.super_path = super_path
        self.no_use = list()
        self.node = dict()

    def __str__(self):
        return self.class_name

    def add_node(self, info):
        self.node[info['function_name']] = info

    def get_node(self, function_name):
        if function_name in self.node:
            return self.node[function_name]
        else:
            if function_name not in self.no_use:
                print "className: " + self.class_name + "." + function_name + " NOT FOUND"
            return None

    def add_no_use(self, function_name):
        self.no_use.append(function_name)

    def get_super_path(self):
        return self.super_path


def get_files(dir_name, end_regx):
    all_file = list()
    for e in os.listdir(dir_name):
        cur_file_name = dir_name + '/' + e
        if e.endswith(end_regx):
            all_file.append(cur_file_name)
        elif os.path.isdir(cur_file_name):
            all_file.extend(get_files(cur_file_name, end_regx))
    return all_file


def get_shop_path_node(file_name):
    f = open(file_name)
    lines = f.readlines()
    path_node = None
    path = None
    method = None
    cache_control = None
    start_annotation = False
    class_name = file_name[file_name.rindex('/') + 1:-len('Service.java')]
    ret_node = None
    if class_name in ['AppAnalyze']:
        lines = lines[0].replace('\r', '\n').split('\n')
    for l in lines:
        if '*/' in l:
            start_annotation = False
        if start_annotation or l.lstrip().startswith('//') or l.startswith('import'):
            continue
        if '@Path(' in l:
            path = l[l.rindex('(') + 2:l.rindex('"')]
            if not path_node:
                path_node = PathNode(class_name, path)
                ret_node = path_node
        elif '@GET' in l:
            method = 'GET'
        elif '@POST' in l:
            method = 'POST'
        elif '@PUT' in l:
            method = 'PUT'
        elif '@CacheControl' in l:
            cache_control = l.lstrip()
            cache_control = cache_control.rstrip()
        elif 'PagingResult' in l or 'Result' in l:
            s = l[:l.index('(')]
            function_name = s[s.rindex(' ') + 1:]
            if path:
                info = dict()
                info['path'] = path
                path = None
                info['function_name'] = function_name
                if not method:
                    method = 'GET'
                info['method'] = method
                method = None
                if cache_control:
                    info['cache_control'] = cache_control
                    cache_control = None
                path_node.add_node(info)
            else:
                path_node.add_no_use(function_name)

        elif '/**' in l:
            start_annotation = True
    f.close()
    return class_name, ret_node


def stall_controller_node(shop_path, file_name):
    f = open(file_name)
    lines = list()
    start_annotation = False
    class_name = file_name[file_name.rindex('/') + 1:-len('Controller.java')]
    if class_name not in shop_path:
        print '可能新加的文件，没有找到该Controller: ' + file_name[file_name.rindex('/') + 1:] + ' Not Found!!'
        return
    path_node = shop_path[class_name]
    add_cache_cont = False
    for l in f.readlines():
        if '/**' in l:
            start_annotation = True
        elif '*/' in l:
            start_annotation = False
        if start_annotation or l.startswith('import') or l.lstrip().startswith('//'):
            lines.append(l)
            continue
        if 'public class ' in l:
            lines.append('@RequestMapping(value = "%s")\n' % path_node.get_super_path())
        if 'public' in l and ('PagingResult' in l or 'Result' in l):
            method = l[:l.index('(')]
            method = method[method.rindex(' ') + 1:]
            info = path_node.get_node(method)
            if info:
                lines.append('    @RequestMapping(value = "' + info[
                    'path'] + '", produces = MediaType.APPLICATION_JSON_VALUE,')
                if info['method'] != 'GET':
                    lines.append('\n            consumes = MediaType.APPLICATION_JSON_VALUE,')
                lines.append(' method = RequestMethod.' + info['method'] + ')\n')
                lines.append('    @ResponseBody\n')
                if 'cache_control' in info:
                    lines.append('    ' + info['cache_control'] + '\n')
                    add_cache_cont = True
                if info['method'] == 'POST' or info['method'] == 'PUT':
                    index = l.index('(')
                    l = l[:index] + '(@RequestBody ' + l[index + 1:]
                if '{' in info['path']:
                    print '@PathVariable, %sController.%s' % (class_name, method)
        lines.append(l)
    if add_cache_cont:
        lines.insert(2, 'import java.util.concurrent.TimeUnit;\n')
        lines.insert(2, 'import com.tqmall.tqmallstall.tools.CacheControl;\n')
    lines.insert(2, 'import org.springframework.web.bind.annotation.*;\n')
    lines.insert(2, 'import org.springframework.http.MediaType;\n')
    f.close()
    new_file = open(file_name, 'w+')
    new_file.writelines(lines)
    new_file.close()


def path_interface():
    shop_path = dict()
    for e in get_files('/Users/xing/code/tqmall/shop/shared/src/main/java/com/tqmall/shop/service',
                       'OrderRemoteService.java'):
        k, v = get_shop_path_node(e)
        if v:
            shop_path[k] = v
    for e in get_files(
            '/Users/xing/code/tqmall/tqmallstall/tqmallstall-web/src/main/java/com/tqmall/tqmallstall/service',
            'OrderRemoteController.java'):
        stall_controller_node(shop_path, e)


def remove_param():
    for e in get_files('/Users/xing/code/tqmall/tqmallstall/tqmallstall-biz/src/main/java/com/tqmall/tqmallstall/param',
                       'Param.java'):
        f = open(e)
        lines = list()
        need_write = False
        for l in f.readlines():
            if '@QueryParam(' in l or 'rs.QueryParam;' in l or 'rs.FormParam;' in l or '@FormParam(' in l:
                need_write = True
                continue
            lines.append(l)
        f.close()
        if need_write:
            new_file = open(e, 'w+')
            new_file.writelines(lines)
            new_file.close()

