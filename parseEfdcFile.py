"""
读取样本文件模块：读网格中心和四角左边，读网格中心浓度

"""
import fileinput
import linecache
import re
import utm


def read_corners(file,config):
    """
    解析EFDC的corners.inp文件中四角坐标

    :param dir: 文件
    :param is_geographic:
    :param kwargs:
    :return:
    """
    """
    解析EFDC的corners.inp文件中四角坐标

    :param dir: lxly.inp文件所在的目录
    :param zone_number: 当前项目所在UMT的分度带
    :return:
    """
    # corners = []
    row_column = []
    lon_lat =[]
    is_convert = False
    if 'is_convert' in config['efdc'] and config['efdc']['is_convert'] == 'True':
        is_convert =True
    with fileinput.input(files=file) as f:
        for line in f:
            if fileinput.lineno() <= 2:
                continue
            split = re.split("\\s+", line)
            corner = {}
            corner_coordinate = []

            for i in range(1, 11, 2):

                if i == 1:
                    # corner["row_column"] = (int(split[i]), int(split[i + 1]))
                    row_column.append((int(split[i]), int(split[i + 1])))
                else:

                    if is_convert and 'zone_number' in config['efdc'] and 'zone_letter' in config['efdc']:
                        u = utm.to_latlon(float(split[i]), float(split[i + 1]), int(config['efdc']['zone_number']), config['efdc']['zone_letter'])
                        corner_coordinate.append((u[1], u[0]))
                    else:
                        corner_coordinate.append((float(split[i]), float(split[i + 1])))
            # corner['corner_coordinate'] = corner_coordinate
            lon_lat.append(corner_coordinate)
            # corners.append(corner)
    return row_column, lon_lat


def read_lxlyinp(file, config):
    """
    解析EFDC的lxly.inp文件中中心坐标

    :param dir: lxly.inp文件所在的目录
    :param zone_number: 当前项目所在UMT的分度带
    :return:
    """
    row_column = []
    lon_lat = []
    with fileinput.input(files=file) as f:
        for line in f:
            if fileinput.lineno() <= 4:
                continue
            split = re.split("\\s+", line)
            if 'zone_number' in config['efdc'] and 'zone_letter' in config['efdc']:
                u = utm.to_latlon(float(split[3]), float(split[4]), int(config['efdc']['zone_number']), config['efdc']['zone_letter'])
                row_column.append((int(split[1]), int(split[2])))
                lon_lat.append((u[1], u[0]))
            else:
                row_column.append((int(split[1]), int(split[2])))
                lon_lat.append((float(split[3]), float(split[4])))
    return row_column, lon_lat


def read_eewq(dir, starrow, endrow):
    """
    EFDC的输出的EE_WQ.TXT文件。

    :param dir: 文件所在的路径
    :param starrow: 解析文件的起始行，从1开始数
    :param endrow:  解析文件的结束行，从1开始数
    :return: 返回网格对的值。
    """
    z_data = []
    file = dir + "EE_WQ.TXT"
    with open(file, "r") as wq:
        for i in wq.readlines()[(starrow - 1):endrow]:
            split = re.split("\\s+", i)
            del split[0]
            del split[len(split) - 1]
            z1 = list(map(float, split))
            z_data.append(z1)
    return z_data


def parse_data(data_str):
    """
    对EFDC的输出文件EE_WQ.TXT的指标数据一行进行拆分，并返回处理的结果数据。

    :param data_str: 指标行的字符串数据。
    :return: 返回一行某一指标数据，是list的float数据。
    """
    split = re.split("\\s+", data_str)
    del split[0]
    del split[len(split) - 1]
    z_data = list(map(float, split))
    return z_data

def getfactors(file_path):
    """
    获取指标
    :param file_path:  文件EE_WQ.txt路径
    :return: 返回开启的指标
    """
    factor_open = []
    factors = ['CHC', 'CHD', 'CHG', 'ROC', 'LOC', 'DOC', 'ROP', 'LOP', 'DOP', 'P4D', 'RON', 'LON', 'DON', 'NHX', 'NOX',
               'SUU', 'SAA', 'COD', 'DOX', 'TAM', 'FCB']
    line = linecache.getline(file_path, 4)
    split = re.split("\\s+", line)
    del split[0]
    del split[len(split) - 1]
    z_data = list(map(int, split))
    for index, value in enumerate(z_data):
        if value == 1:
            factor_open.append(factors[index])
    return factor_open