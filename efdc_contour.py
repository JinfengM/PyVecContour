"""
函数入口
"""
import fileinput
import os.path
import sys
import time
import configparser
import numpy as np

from parseEfdcFile import read_lxlyinp, getfactors, parse_data, read_corners
from result_output import save2file, result2mysqldb, result2csv
from rotateAndContor import computer_contourf

if __name__ == '__main__':
    # print("温馨提示：后面不带配置文件路径就读取默认同级目录下的config.ini")
    #*****************************************参数判断*****************************************
    config_path = "config.ini"
    if len(sys.argv) == 2:
        if not os.path.exists(sys.argv[1]):
            print("配置文件不存在")
            sys.exit(0)
        else:
            config_path = sys.argv[1]
    if len(sys.argv) >= 3:
        print("只接收一个参数配置文件路径")
        sys.exit(0)
    if len(sys.argv)==1 and not os.path.exists("config.ini"):
        print("配置文件必须提供")
        sys.exit(0)
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    # dir = "G:\\1ashuzhongguo\\work\\中科院\Lake_T_HYD_WQ\\"

    lxlyinp_path = config["efdc"]["home"]
    if "lxlyinp_path" in config["efdc"]:
        lxlyinp_path = config["efdc"]["lxlyinp_path"]
    if not os.path.exists(lxlyinp_path):
        print("lxly.inp文件的目录不存在")
        sys.exit(0)

    corner_path = config["efdc"]["home"]
    if "corner_path" in config["efdc"]:
        corner_path = config["efdc"]["corner_path"]
    if not os.path.exists(corner_path):
        print("corner.inp文件的目录不存在")
        sys.exit(0)
    # *****************************************解析文件xly.inp文件*****************************************
    # row_column, center_coordinate = read_lxlyinp(dir=lxlyinp_path, zone_number=int(config["efdc"]["zone_number"]), zone_letter=config["efdc"]["zone_letter"])
    corner_row_column, corner_coordinate= read_corners(corner_path, config)
    center_row_column, center_coordinate = read_lxlyinp(lxlyinp_path, config)
    order_center_coordinate = []
    # order_center_coordinate = center_coordinate
    for corner in corner_row_column:
        for center, coordinate in zip(center_row_column, center_coordinate):
            if corner == center:
                order_center_coordinate.append(coordinate)
    # fo = open(config['contour']['contour_dir'] +"lxly_order.csv", "w")
    # fo.write("X,Y\n")
    # for coordinate in order_center_coordinate:
    #     fo.write(str(coordinate[0])+","+str(coordinate[1])+"\n")
    # fo.flush()
    # fo.close()
    ee_wq_path = config["efdc"]["home"] + "#output/EE_WQ.TXT"
    if "eewq_path" in config["efdc"]:
        ee_wq_path = config["efdc"]["eewq_path"]
    if not os.path.exists(lxlyinp_path):
        print("EE_WQ.TXT文件的目录不存在")
        sys.exit(0)
    x = [coordinate[0] for coordinate in order_center_coordinate]
    y = [coordinate[1] for coordinate in order_center_coordinate]
    #通过解析文件ee_wq.txt文件的第四行获取，获取模拟因子。
    # *****************************************获取模拟因子*****************************************
    factors = getfactors(file_path=ee_wq_path)
    computer_time = ""
    time_row = 0
    # dir = "G:\\test\\conourf\\"
    with fileinput.input(files=ee_wq_path) as f:
        for line in f:
            # print("开始=============================》")
            print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
            if 'end_row' in config['contour'] and fileinput.lineno() >= int(config['contour']['end_row']):
                sys.exit(0)
            if fileinput.lineno() >= 5 and (fileinput.lineno() == 5 or (fileinput.lineno() - 5) % (len(factors) + 1) == 0):
                computer_time = line.strip('[ \n]')
                time_row = fileinput.lineno()
                continue
            if int(config['contour']['start_row']) < 5:
                print('解析起始行要大于等于5')
                sys.exit(0)
            if fileinput.lineno() >= int(config['contour']['start_row']):
                print("===============》第" + str(fileinput.lineno()) + "行")
                factor_index = fileinput.lineno() - time_row - 1
                z_data = parse_data(line)
                if min(z_data) == max(z_data):
                    print("最大值与最小值相等为" + str(max(z_data)))
                    continue
                else:
                    time_str = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
                    # print("====================》文件名：" + factors[factor_index] + "_" + computer_time + "-" + time_str)
                    levels = []
                    if 'levels' in config['contour']:
                        levels = [round(float(level), 4) for level in config['contour']['levels'].split(",")]
                    json_contourf, levels, is_rotate = computer_contourf(x=x, y=y, z=z_data, levels=levels, config=config)
                    if not os.path.exists(config['contour']['contour_dir']):
                        print("输出目录不存在")
                        sys.exit(0)
                    fo = open(config['contour']['contour_dir'] + factors[factor_index] + "_" + computer_time+"_levels.txt", "w")
                    levels_str = ','.join([str(i) for i in levels])
                    fo.write("[" + levels_str + "]")
                    fo.flush()
                    fo.close()
                    file_type = 'pbf'   
                    if 'file_type' in config['contour']:
                        file_type = config['contour']['file_type']
                    fname = "cropped_"+factors[factor_index] + "_" + computer_time if is_rotate else "uncropped_"+factors[factor_index] + "_" + computer_time
                    file_path = save2file(data=json_contourf,
                                          fname=fname, dir=config['contour']['contour_dir'],
                                          out_type=file_type)
                    if 'out_type' in config['output'] and 'mysql' == config['output']['out_type']:
                        result2mysqldb(config=config, factor=factors[factor_index], time=computer_time, path=file_path)
                    else:
                        result2csv(factors[factor_index], computer_time, file_path, config['contour']['contour_dir'] + "contour_result.csv")
            # print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
            # print("结束《=============================")