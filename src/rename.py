# -*- coding: UTF-8 -*-
__author__ = 'xing'

import os

if __name__ == '__main__':
    workspace = '/Users/xing/code/tqmall/'
    model_dir = workspace + 'shop/shared/src/main/java/com/tqmall/shop/model/'
    xml_mapper_dir = workspace + 'shop/server/src/main/resources/com/tqmall/shop/mapper'
    java_mapper_dir = workspace + 'shop/server/src/main/java/com/tqmall/shop/mapper'
    for f in os.listdir(model_dir):
        if f.endswith('BO.java') or not f.endswith('.java') or not f.startswith('Seller'):
            continue
        print 'rename: ' + f
        old_model_file = open(model_dir + f, 'r')
        new_class_name = f[:-5] + 'BO'
        new_model_file = open(model_dir + new_class_name + '.java', 'w')
        need_w = True
        new_lines = list()
        count = 0
        for l in old_model_file.readlines():
            if 'class' in l:
                l = l.replace(f[:-5], new_class_name)
                new_lines.append('import lombok.Data;\n\n@Data\n')
            elif 'public' in l:
                need_w = False
                count = 0
            if need_w:
                new_lines.append(l)
            elif count <= 4:
                count += 1
            else:
                need_w = True
        new_lines.append('}')
        old_model_file.close()
        new_model_file.writelines(new_lines)
        new_model_file.close()
        os.remove(model_dir + f)
