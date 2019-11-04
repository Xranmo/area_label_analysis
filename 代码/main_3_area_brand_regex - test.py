# 1104 横向判断+dict


# coding=utf-8
import re
import pandas as pd
import time

judge = pd.read_csv(r"C:\Users\sunsharp\Desktop\吴枭\区域公共品牌\2019.10\数据源\data.csv")

GeoProdData = pd.read_csv(r"C:\Users\sunsharp\Desktop\吴枭\区域公共品牌\2019.10\数据源\地理标志产品.csv")
NotGeoProdData = pd.read_csv(r"C:\Users\sunsharp\Desktop\吴枭\区域公共品牌\2019.10\数据源\非地理标志产品.csv")



# #----------------------------------
# #下面是字典转化的前置工作
# #----------------------------------


#将GeoProdData转化为字典形式：{'梅山猪':['嘉定'],'白茶':['黄山','正安'],'他留乌骨鸡':''} ，所以是包含三种情况
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

#将NotGeoProdData转化为字典形式
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

# #----------------------------------
# #下面是辅助函数
# #----------------------------------

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


# #----------------------------------
# #下面为正式解析函数
# #----------------------------------


# 判断是否存在特产品字段
def get_SpecialProd(temp):
    if re.search(r'特产品类":"(.*?)"', temp) is not None:
        if re.search(r'特产品类":"(.*?)"', temp).group(1) not in ['其他','其它']:  # 有的特产品类标记为：其他
            return re.search(r'特产品类":"(.*?)"', temp).group(1)

# 地理标志产品字段解析
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

def get_NotGeoProd(temp):
    NotGeoProdlist = {}
    for k, area_labels in not_geo_map.items():
        if k in temp:
            for area_label in area_labels:
                if area_label == '':
                    NotGeoProdlist[k] = ''
                elif area_label in temp:
                    NotGeoProdlist[area_label+k] = area_label
                    #这里实际上应当返回对应的product的名字，而不是area_label+prod_label的名字，所以之后还可以在优化
    if len(NotGeoProdlist) > 0:
        return NotGeoProdlist

# 最终解析结果
def regex(obj):

    sepcial_name = None
    Geodict = None
    NotGeodict = None
    final_Prod = None
    final_label =0

    prod_detail = obj['prod_detail']
    prod_name = obj['prod_name']
    sepcial_name = get_SpecialProd(prod_detail)


    # 存在特产品类就以特产品类为最终结果
    if sepcial_name is not None:
        final_Prod = sepcial_name
        final_label = 1

        # 不存在特产品类就尝试以地理标志产品为最终结果
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

        # 不存在地理标志产品则尝试以非地理标志产品为最终结果
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
    return sepcial_name,Geodict,NotGeodict,final_Prod,final_label


if __name__ == '__main__':

    time_start = time.time()  # 开始计时

    judge = judge[:1000]
    print('原始数据共有%d行' % judge.shape[0])

    data=[]
    for i in range(judge.shape[0]):
        obj=judge.loc[i]
        id=obj['id']
        sepcial_name,Geodict,NotGeodict,final_Prod,final_label = regex(obj)
        if (i % 100) == 0:
            print('完成%s行' % i)
        data.append([id, sepcial_name,Geodict,NotGeodict,final_Prod,final_label])
    data_df = pd.DataFrame(data, columns=['id', 'sepcial_name','Geodict','NotGeodict','final_Prod','final_label'])
    result=pd.merge(judge,data_df,left_on='id',right_on='id')
    result.to_csv(r"C:\Users\sunsharp\Desktop\吴枭\区域公共品牌\2019.10\结果输出\result.csv")


    time_end = time.time()  # 结束计时
    time_c = time_end - time_start  # 运行所花时间
    print('time cost', time_c, 's')

