"""
    采样空间旋转：旋转研究区，求面积最小角度，插值绘制等值线
    空间剪切模块，抠岛或多个岛
"""
import os
import sys

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import rgb2hex
from geojson import Polygon, FeatureCollection, Feature
import geopandas as gpd
from pykrige import OrdinaryKriging
import matplotlib.tri as tri
from shapely.geometry import Point, box
from functools import  reduce
import operator


def convert(gridx, gridy, gridz, levels):
    """
    matplotlib 的 contours产生的等值面转geojson

    :param gridx: 网格x数组
    :param gridy: 网格y数学
    :param gridz: 网格坐标对应的属性值
    :param levels: 绘制成等值面的阈值
    :return:  geojson格式
    """
    figure = plt.figure()
    ax = figure.add_subplot(111)
    cntr = ax.contour(gridx, gridy, gridz)
    ax.clabel(cntr, fmt="%1.2f", use_clabeltext=True)
    contourf = ax.contourf(gridx, gridy, gridz, levels=levels, cmap=plt.cm.jet)
    plt.show()

    polygon_features = []
    for index, collection in enumerate(contourf.collections):
        color = collection.get_facecolor()
        for path in collection.get_paths():
            v = path.vertices
            if len(v) < 3:
                continue
            for coord in path.to_polygons():
                polygon = Polygon(coordinates=[coord.tolist()])
                properties = {
                    "contour_value": contourf.levels[index],
                    "level_index": index,
                    "stroke": rgb2hex(color[0])
                }
                feature = Feature(geometry=polygon, properties=properties)
                polygon_features.append(feature)
    feature_collection = FeatureCollection(polygon_features)
    plt.cla()
    plt.clf()
    plt.close()
    return feature_collection


def min_area_rotate(x, y, crs):
    """
    通过指定的角度不断循环，然后找出面积最小的角度。
    :param crs: 坐标系统
    :param x:  离散点的坐标x数组
    :param y:  离散点的坐标y数组
    :return:   area旋转每次旋转的面积和对应旋转角度的列表 origin旋转点，最小面积的x,y
    """
    origin = (x[0], y[0])
    geom = gpd.GeoSeries([Point(x1, y1) for x1, y1 in zip(x, y)], [index for index in range(0, len(x), 1)], crs)
    area = []
    for i in range(0, 91, 1):
        my_rotate = geom.rotate(i, origin=origin)
        my_area = gpd.GeoSeries([box(*my_rotate.total_bounds.tolist())])
        area.append((my_area.area[0], i))
    geom_rotate = geom.rotate(min(area)[1], origin=origin)
    # print(geom_rotate.head())
    # 求出最小面积之后，给x,y赋值
    x_rotate = [point.x for point in geom_rotate.tolist()]
    y_rotate = [point.y for point in geom_rotate.tolist()]
    return area, origin, x_rotate, y_rotate


def computer_contourf(x, y, z, levels, config):
    """
    计算等值线：1 is_rotate = true.选择旋转求出最小面积，然后在进行插值，通过插值，计算等值线，
    然后再旋转边界，进行裁剪，最后在旋转到原来的位置。
              2.is_rotate = flase 不选择旋转，直接进行插值，计算等值线，利用边界裁剪。
              3.可以裁剪边界中有可以任意多个空洞，裁剪的结果都是交集。
    :param x:  离散点的坐标x数组
    :param y:  离散点的坐标y数组
    :param z:  离散点坐标上的z值数组
    :param levels:  绘制等值线的个数或等值线的z数组
    :param config:  配置参数参数集
    :return:  返回geojson字符串是研究区范围内的等值线结果
    """
    if "border_path" in config['contour'] and os.path.exists(config['contour']['border_path']):
        border_path = config['contour']['border_path']
    else:
        print("边界文件必须输入参数")
        sys.exit(0)

    is_rotate = False
    if 'is_rotate' in config['contour']:
        is_rotate = config['contour']['is_rotate']

    row = 200
    if 'row' in config['contour']:
        row = int(config['contour']['row'])

    column = 200
    if 'column' in config['contour']:
        column = int(config['contour']['column'])

    variogram_model = 'gaussian'
    if 'variogram_model' in config['contour']:
        variogram_model = config['contour']['variogram_model']

    crs = "EPSG:4326"
    if 'crs' in config['contour']:
        crs = config['contour']['crs']

    coordinates_type = "euclidean"
    if 'coordinates_type' in config['contour']:
        coordinates_type = config['contour']['coordinates_type']

    nlags = 6
    if 'nlags' in config['contour']:
        nlags = int(config['contour']['nlags'])

    level_number = 11
    if 'level_number' in config['contour']:
        level_number = int(config['contour']['level_number'])

    if is_rotate:
        area, origin, x, y = min_area_rotate(x, y, crs)

    gridx = np.linspace(min(x), max(x), column)
    gridy = np.linspace(min(y), max(y), row)
    if 'delta' in config['contour']:
        gridx = np.arange(min(x), max(x), float(config['contour']['delta']))
        gridy = np.arange(min(y), max(y), float(config['contour']['delta']))
    ok = OrdinaryKriging(x, y, z, variogram_model=variogram_model, coordinates_type=coordinates_type, nlags=nlags, pseudo_inv=True)
    Zi, ss = ok.execute("grid", gridx, gridy)
    Zi[Zi < 0] = 0
    Xi, Yi = np.meshgrid(gridx, gridy)
    if len(levels) == 0:
        index_max = np.unravel_index(Zi.argmax(), Zi.shape)
        index_min = np.unravel_index(Zi.argmin(), Zi.shape)
        levels = np.linspace(Zi[index_min[0], index_min[1]]*0.99, Zi[index_max[0], index_max[1]]*1.01, level_number)
        levels = [round(i, 4) for i in levels]
    contourf = convert(Xi, Yi, Zi, levels)
    # data = geojson.dumps(contourf, sort_keys=True, separators=(',', ':'))

    gdf = gpd.GeoDataFrame.from_features(contourf["features"], crs)
    if is_rotate:
        gdf = gpd.GeoDataFrame({"contour_value": gdf['contour_value'], "level_index": gdf['level_index'], "stroke": gdf['stroke']}, geometry=gdf.rotate(-min(area)[1], origin=origin), crs=crs)
    file = open(border_path)
    gpd_border = gpd.read_file(file).set_crs(crs)

    # fo = open(config['contour']['contour_dir'] + "contour_unclip.json", "w")
    # fo.write(gdf.to_json())
    # fo.flush()
    # fo.close()
    # 这里裁剪之后顺序乱了，顺序必须是level的升序，从低到搞排序。如果顺序是乱的可能会导致某些环不能显示，被覆盖。
    result = gdf.clip(gpd_border, True).sort_values(by='level_index')
    # result = gpd.clip(gdf, gpd_border)
    # print("===================================以下是结果========================================")
    # print(result.head())
    result_str = result.to_json(drop_id=True)
    return result_str, levels, is_rotate
