# coding=utf-8
import records
import re
import pandas as pd
import time

# from numba import jit


db = records.Database('postgresql://hexuejian:4ZiN0CXq9M16@47.99.138.41:5432/warehouse')

select_table = 'mining_testdb.areabrand2018_1102'
sql = " SELECT id,prod_name,prod_detail FROM {}".format(select_table)


GeoProdData =pd.read_excel(r'source.xlsx',sheet_name='dili')
NotGeoProdData = pd.read_excel(r'source.xlsx',sheet_name='feidili')

# 判断是否存在特产品字段
def get_SpecialProd(temp):
    if re.search(r'特产品类":"(.*?)"', temp) is not None:
        if re.search(r'特产品类":"(.*?)"', temp).group(1) not in ['其他','其它']:  # 有的特产品类标记为：其他
            return re.search(r'特产品类":"(.*?)"', temp).group(1)



geo_map = {}
for i in range(GeoProdData.shape[0]):
    area_label = str(GeoProdData.area_label[i])
    prod_label = str(GeoProdData.prod_label[i])
    if area_label != 'nan':
        try:
            area_labels = geo_map[prod_label]
            area_labels.append(area_label)
        except:
            area_labels = []
            area_labels.append(area_label)
            geo_map[prod_label] = area_labels
    else:
        try:
            area_labels = geo_map[prod_label]
            area_labels.append('')
        except:
            area_labels = []
            area_labels.append('')
            geo_map[prod_label] = area_labels

# @jit
def get_GeoProd(temp):
    GeoProdlist = {}
    for k,area_labels in geo_map.items():
        if k in temp:
            for area_label in area_labels:
                if area_label == '':
                    GeoProdlist[k] = ''
                elif area_label in temp:
                    GeoProdlist[area_label+k] = area_label
    if len(GeoProdlist) > 0:
        return GeoProdlist

def get_Geodetail(prod_detail):  # 用i来限制输入的是series
    if re.search(r'省份":"(.*?)省', prod_detail) is not None:
        province = re.search(r'省份":"(.*?)省', prod_detail).group(1)
    else:
        province = '这就是一个不可能匹配成功的字符串'

    if re.search(r'城市":"(.*?)市', prod_detail) is not None:
        city = re.search(r'城市":"(.*?)市', prod_detail).group(1)
    else:
        city = '这就是一个不可能匹配成功的字符串'

    return [province, city]

def get_dictproduct(proddict, area):
    for i, j in proddict.items():
        if j in area:
            return i


not_geo_map = {}
for i in range(NotGeoProdData.shape[0]):
    area_label = str(NotGeoProdData.area_label[i])
    prod_label = str(NotGeoProdData.prod_label[i])
    if area_label != 'nan':
        try:
            area_labels = not_geo_map[prod_label]
            area_labels.append(area_label)
        except:
            area_labels = []
            area_labels.append(area_label)
            not_geo_map[prod_label] = area_labels
    else:
        try:
            area_labels = not_geo_map[prod_label]
            area_labels.append('')
        except:
            area_labels = []
            area_labels.append('')
            not_geo_map[prod_label] = area_labels

# @jit
def get_NotGeoProd(temp):
    NotGeoProdlist = {}
    for k, area_labels in not_geo_map.items():
        if k in temp:
            for area_label in area_labels:
                if area_label == '':
                    NotGeoProdlist[k] = ''
                elif area_label in temp:
                    NotGeoProdlist[area_label+k] = area_label
    if len(NotGeoProdlist) > 0:
        return NotGeoProdlist

# @jit
def regex(obj):
    final_Prod = None
    final_label = None

    prod_detail = obj['prod_detail']
    prod_name = obj['prod_name']
    sepcial_name = get_SpecialProd(prod_detail)
    if sepcial_name is not None:
        final_Prod = sepcial_name
        final_label = 1
    else:
        Geodict= get_GeoProd(prod_name)

        if Geodict is not None:

            province, city = get_Geodetail(prod_detail)  # 获取省份、城市信息

            if len(Geodict) == 1:  # 只有一个字典，则默认为是准确值
                final_Prod = list(Geodict.keys())[0]
                final_label = 2
            else:  # 多个字典，引入地域判断
                if city in list(Geodict.values()):
                    final_Prod = get_dictproduct(Geodict, city)
                    final_label = 2
                elif province in list(Geodict.values()):
                    final_Prod = get_dictproduct(Geodict, province)
                    final_label = 2
                else:
                    final_label = -1  # -1表示存在多个可选项，但是都不够精确，因此只能人工筛选

        else:
            NotGeodict = get_NotGeoProd(prod_name)
            if NotGeodict is not None:
                province, city = get_Geodetail(prod_detail)  # 获取省份、城市信息
                if len(NotGeodict) == 1:  # 只有一个字典，则默认为是准确值
                    final_Prod = list(NotGeodict.keys())[0]
                    final_label = 3
                else:
                    if city in list(NotGeodict.values()):
                        final_Prod = get_dictproduct(NotGeodict, city)
                        final_label = 3
                    elif province in list(NotGeodict.values()):
                        final_Prod = get_dictproduct(NotGeodict, province)
                        final_label = 3
                    else:
                        final_label = -2  # -2表示存在多个可选项，但是都不够精确，因此只能人工筛选
    return final_Prod,final_label


if __name__ == '__main__':

    insert_table = 'areabrand2018_1102_result'

    time_start = time.time()
    rows = db.query(sql)
    rows = rows.all(as_dict=True)
    time_end = time.time()  # 结束计时
    time_c = time_end - time_start  # 运行所花时间
    print('sql time cost', time_c, 's')
    data = []
    time_start = time.time()  # 开始计时
    i = 0;
    for row in rows:
        id = row['id']
        final_Prod, final_label = regex(row)
        data.append([id, final_Prod, final_label])
        i=i+1
        if (i% 1000 == 0):
            print(i)
    result = pd.DataFrame(data, columns=['id', 'final_Prod', 'final_label'])
    time_end = time.time()  # 结束计时
    time_c = time_end - time_start  # 运行所花时间
    print('time cost', time_c, 's')
