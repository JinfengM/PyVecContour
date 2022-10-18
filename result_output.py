# -*- coding: UTF-8 -*-
"""
    文件格式转换模块，结果文件输出probuf格式。

"""
import json
import os
import re
import sys
import uuid

import geobuf
import pymysql


def save2file(dir, fname, data, **kwargs):
    """
    把等值线的结果存储到文件,输出到json文件或pbf文件

    :param dir:  文件所属目录
    :param fname:  文件名
    :param data:   结果数据
    :param out_type:  输出类型 只可以输出入geojson或pbf,默认输出到pbf
    :return:  返回文件路径
    """
    if "out_type" in kwargs and kwargs['out_type'] == 'json':
        filepath = dir + fname + ".json"
        fo = open(filepath, "w")
        fo.write(data)
        fo.close()
    else:
        filepath = dir + fname + ".pbf"
        pbf = geobuf.encode(json.loads(data))
        fo = open(filepath, "wb+")
        fo.write(pbf)
        fo.close()
    return filepath


def result2mysqldb(config,factor, time, path):
    """
    把指标对应时间下生成的绘制的等值线文件路径之间对应关系存储到数据库

    :param factor:  模型计算指标名
    :param time:    模型计算时间
    :param path:    等值线文件存放位置
    :return:
    """
    # Connect to the database
    host='localhost'
    user='root'
    port='3306'

    if 'host' in config['db']:
        host = config['db']['host']
    if 'user' in config['db']:
        user = config['db']['user']
    if 'password' not in config['db']:
        print('用户密码必须提供')
        sys.exit(0)
    if 'port' in config['db']:
        port = config['db']['port']
    if 'database' not in config['db']:
        print("连接的数据库名，必须提供")
        sys.exit(0)
    connection = pymysql.connect(host=host,
                                 user=user,
                                 port=port,
                                 password=config['db']['password'],
                                 database=config['db']['database'],
                                 cursorclass=pymysql.cursors.DictCursor)
    sql = "INSERT INTO `tb_eewq` (`id`, `factor`,`time`,`path`) VALUES (%s, %s,%s, %s)"
    id = str(uuid.uuid4().hex)
    cursor = connection.cursor()
    try:
        cursor.execute(sql, (id, factor, time, path))
        connection.commit()
    except:
        # Rollback in case there is any error
        connection.rollback()
    cursor.close()
    connection.close()


def result2csv(factor, time, path, out_path):
    """
    把指标在指定时间下的等值线存储路径，三个关系存储到csv中

    :param factor:  模型计算指标名
    :param time:    模型计算时间
    :param path:    等值线文件存放位置
    :param out_path:    csv文件路径
    :return:
    """
    if not os.path.exists(out_path[0:out_path.rindex('/')]):
        os.makedirs(out_path[0:out_path.rindex('/')])
    fo = open(out_path, "a")
    title = "id,factor, time, path\n"
    if not os.path.exists(out_path):
        fo.write(title)
    id = str(uuid.uuid4().hex)
    data = f'{id},{factor}, {time}, {path}\n'
    fo.write(data)
    fo.close()


# if __name__ == '__main__':
#     result2csv("sss", "sss", "sss", "G:/test/szgmmm/szgsss/test.csv")