#1030版   横向版
# coding=utf-8

import pandas as pd
import re

judge = pd.read_csv(r"C:\Users\sunsharp\Desktop\吴枭\区域公共品牌\2019.10\数据源\data.csv")

GeoProdData = pd.read_csv(r"C:\Users\sunsharp\Desktop\吴枭\区域公共品牌\2019.10\数据源\地理标志产品.csv")
NotGeoProdData = pd.read_csv(r"C:\Users\sunsharp\Desktop\吴枭\区域公共品牌\2019.10\数据源\非地理标志产品.csv")


# 提取信息字段里的省份和城市
def get_Geodetail(judge, i):  # 用i来限制输入的是series
    if re.search(r'省份":"(.*?)省', judge.prod_detail[i]) is not None:
        province = re.search(r'省份":"(.*?)省', judge.prod_detail[i]).group(1)
    else:
        province = '这就是一个不可能匹配成功的字符串'

    if re.search(r'城市":"(.*?)市', judge.prod_detail[i]) is not None:
        city = re.search(r'城市":"(.*?)市', judge.prod_detail[i]).group(1)
    else:
        city = '这就是一个不可能匹配成功的字符串'

    return [province, city]


# 提取字典里符合地域key值的value，如果一个key存在多个value，那么会根据循环规则只返回第一个
def get_dictproduct(proddict, area):
    for i, j in proddict.items():
        if j == area:
            return i


# #----------------------------------
# #以上为辅助函数，下面为正式解析函数
# #----------------------------------


# 特产品类字段解析
def get_SpecialProd(temp):
    # 判断是否存在特产品字段
    if re.search(r'特产品类":"(.*?)"', temp) is not None:
        if re.search(r'特产品类":"(.*?)"', temp).group(1) != '其他':  # 有的特产品类标记为：其他
            return re.search(r'特产品类":"(.*?)"', temp).group(1)


# 地理标志产品字段解析
# 品牌库分词不准确
def get_GeoProd(temp):
    GeoProdlist = {}

    for i in range(GeoProdData.shape[0]):
        if str(GeoProdData.area_label[i]) != 'nan':  # 名称有空值为float('nan')格式
            if (str(GeoProdData.area_label[i]) in temp) & (str(GeoProdData.prod_label[i]) in temp):
                GeoProdlist[GeoProdData['product'][i]] = str(GeoProdData.area_label[i])
        elif (str(GeoProdData.prod_label[i]) in temp):
            GeoProdlist[GeoProdData['product'][i]] = ''

    if len(GeoProdlist) > 0:
        return GeoProdlist  # 多个地理标志的情况待优化


# 非地理标志产品字段解析
# 品牌库分词不准确
def get_NotGeoProd(temp):
    NotGeoProdlist = {}

    for i in range(NotGeoProdData.shape[0]):
        if str(NotGeoProdData.area_label[i]) != 'nan':  # 名称有空值为float('nan')格式
            if (str(NotGeoProdData.area_label[i]) in temp) & (str(NotGeoProdData.prod_label[i]) in temp):
                NotGeoProdlist[NotGeoProdData['product'][i]] = str(NotGeoProdData.area_label[i])
        elif (str(NotGeoProdData.prod_label[i]) in temp):
            NotGeoProdlist[NotGeoProdData['product'][i]] = ''

    if len(NotGeoProdlist) > 0:
        return NotGeoProdlist  # 多个地理标志的情况待优化


# 最终结果
def final_Prod(i):
    # 存在特产品类就以特产品类为最终结果
    judge.loc[i, 'SpecialProd'] = get_SpecialProd(judge['prod_detail'][i])
    if judge.loc[i, 'SpecialProd'] is not None:
        judge.loc[i, 'final_Prod'] = judge.loc[i, 'SpecialProd']
        judge.loc[i, 'final_label'] = 1
    else:
        Geodict=(get_GeoProd(judge['prod_name'][i]))
        if Geodict is not None:
            province, city = get_Geodetail(judge, i)  # 获取省份、城市信息
            judge.loc[i, 'GeoProdlist']=str(Geodict)    #df中无法直接得到字典？

            if len(Geodict) == 1:  # 只有一个字典，则默认为是准确值
                judge.loc[i, 'final_Prod'] = list(Geodict.keys())[0]
                judge.loc[i, 'final_label'] = 2
            else:  # 多个字典，引入地域判断
                if city in list(Geodict.values()):
                    judge.loc[i, 'final_Prod'] = get_dictproduct(Geodict, city)
                    judge.loc[i, 'final_label'] = 2
                elif province in list(Geodict.values()):
                    judge.loc[i, 'final_Prod'] = get_dictproduct(Geodict, province)
                    judge.loc[i, 'final_label'] = 2
                else:
                    judge.loc[i, 'final_label'] = -1  # -1表示存在多个可选项，但是都不够精确，因此只能人工筛选

        else:
            NotGeodict = get_NotGeoProd(judge['prod_name'][i])
            if NotGeodict is not None:
                province, city = get_Geodetail(judge, i)  # 获取省份、城市信息
                judge.loc[i, 'NotGeoProdlist']=str(NotGeodict)    #df中无法直接得到字典？

                if len(NotGeodict) == 1:  # 只有一个字典，则默认为是准确值
                    judge.loc[i, 'final_Prod'] = list(NotGeodict.keys())[0]
                    judge.loc[i, 'final_label'] = 3
                else:
                    if city in list(NotGeodict.values()):
                        judge.loc[i, 'final_Prod'] = get_dictproduct(NotGeodict, city)
                        judge.loc[i, 'final_label'] = 3
                    elif province in list(NotGeodict.values()):
                        judge.loc[i, 'final_Prod'] = get_dictproduct(NotGeodict, province)
                        judge.loc[i, 'final_label'] = 3
                    else:
                        judge.loc[i, 'final_label'] = -2  # -2表示存在多个可选项，但是都不够精确，因此只能人工筛选


def start(judge):
    import time
    time_start = time.time()  # 开始计时
    print('原始数据共有%d行' % judge.shape[0])

    judge['SpecialProd'] = ''
    judge['GeoProdlist']=''
    judge['NotGeoProdlist']=''
    judge['final_Prod'] = ''
    judge['final_label'] = 0

    for i in range(judge.shape[0]):
        # if (i % 50) == 0:
        #     print('完成%s行' % i)
        final_Prod(i)  # 最终判断

    judge.to_csv(r"C:\Users\sunsharp\Desktop\吴枭\区域公共品牌\2019.10\结果输出\结果.csv")

    time_end = time.time()  # 结束计时
    time_c = time_end - time_start  # 运行所花时间
    print('time cost', time_c, 's')


judge = judge[:10000]
start(judge)
