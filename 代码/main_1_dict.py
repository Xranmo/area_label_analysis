#1030版   横向字典版

# coding=utf-8

import pandas as pd
import re
import jieba_fast as jieba

judge = pd.read_csv(r"C:\Users\sunsharp\Desktop\吴枭\区域公共品牌\2019.10\数据源\data.csv")

GeoProdData = pd.read_csv(r"C:\Users\sunsharp\Desktop\吴枭\区域公共品牌\2019.10\数据源\地理标志产品.csv")
NotGeoProdData = pd.read_csv(r"C:\Users\sunsharp\Desktop\吴枭\区域公共品牌\2019.10\数据源\非地理标志产品.csv")


#----------------------------------
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


# 提取字典里符合地域value值的key
def get_dictproduct(proddict, area):
    for i, j in proddict.items():
        if j == area:
            return i

#  将品牌库构建成两个字典
def proddict_create(proddata):
    product_dict={}      #示例：{'嘉定梅山猪': {'梅山猪': '嘉定'}}
    area_prod_dict={}   #示例：{'梅山猪': ['嘉定']}  必须是列表形式，因为存在多个
    temp=[]
    for i in range(proddata.shape[0]):
        if proddata.prod_label[i] in area_prod_dict.keys():
            a=area_prod_dict[proddata.prod_label[i]]
            a.append(proddata.area_label[i])
            area_prod_dict[proddata.prod_label[i]]=a
        else:
            area_prod_dict[proddata.prod_label[i]]=[proddata.area_label[i]]

        product_dict[proddata['product'][i]]={proddata.prod_label[i]:proddata.area_label[i]}
    return [product_dict,area_prod_dict]

#----------------------------------
#以上为辅助函数，下面为正式解析函数
#----------------------------------


# 特产品类字段解析
def get_SpecialProd(judge):
    # 判断是否存在特产品字段
    def SpecialProd_judge(temp):
        if re.search(r'特产品类":"(.*?)"', temp) is not None:
            if re.search(r'特产品类":"(.*?)"', temp).group(1) != '其他':  # 有的特产品类标记为：其他
                return re.search(r'特产品类":"(.*?)"', temp).group(1)

    judge['SpecialProd'] = judge.prod_detail.apply(SpecialProd_judge)


# 地理标志产品字段解析
# 品牌库分词不准确
def get_GeoProd(judge):
    def GeoProd_judge(temp):
        GeoProdlist = {}
        Geo_Prod_dict,Geo_area_prod_dict=proddict_create(GeoProdData)

        prod_name_list=list(jieba.cut(temp))

        for i in prod_name_list:
            if i in Geo_area_prod_dict.keys():
                templist=Geo_area_prod_dict[i]
                for j in templist:
                    if j in prod_name_list:
                        tempdict={i:j}   #成功匹配到合适的地域和品牌
                        productname=get_dictproduct(Geo_Prod_dict,tempdict)     #返回Geo_Prod_dict字典寻找对应的品牌名
                        GeoProdlist[productname]=j

        if len(GeoProdlist) > 0:
            return GeoProdlist  # 多个地理标志的情况待优化

    judge['GeoProdlist'] = judge.prod_name.apply(GeoProd_judge)  # 得到一个dict


# 非地理标志产品字段解析
# 品牌库分词不准确
def get_NotGeoProd(judge):
    def NotGeoProd_judge(temp):
        NotGeoProdlist = {}
        NotGeo_Prod_dict,NotGeo_area_prod_dict=proddict_create(NotGeoProdData)

        prod_name_list=list(jieba.cut(temp))           #分词词库有问题，比如中宁枸杞，会分成 中和宁，所以还得自定义添加词库

        for i in prod_name_list:
            if i in NotGeo_area_prod_dict.keys():
                templist=NotGeo_area_prod_dict[i]
                for j in templist:
                    if j in prod_name_list:
                        tempdict={i:j}   #成功匹配到合适的地域和品牌
                        productname=get_dictproduct(NotGeo_Prod_dict,tempdict)     #返回NotGeo_Prod_dict字典寻找对应的品牌名
                        NotGeoProdlist[productname]=j

        if len(NotGeoProdlist) > 0:
            return NotGeoProdlist  # 多个地理标志的情况待优化

    judge['NotGeoProdlist'] = judge.prod_name.apply(NotGeoProd_judge)  # 得到一个dict


# 最终结果
def final_Prod(judge):
    judge['final_Prod'] = judge.SpecialProd
    judge['final_label'] = 0

    for i in range(judge.shape[0]):

        # 存在特产品类就以特产品类为最终结果
        if judge.SpecialProd[i] is not None:
            judge.loc[i,'final_label']= 1

        # 存在地理标志产品就以地理标志产品为最终结果
        elif judge.GeoProdlist[i] is not None:
            province, city = get_Geodetail(judge, i)  # 获取省份、城市信息
            Geodict = judge.GeoProdlist[i]

            if len(Geodict) == 1:  # 只有一个字典，则默认为是准确值
                judge.loc[i,'final_Prod'] = list(Geodict.keys())[0]
                judge.loc[i,'final_label'] = 2
            else:  # 多个字典，引入地域判断
                if city in list(Geodict.values()):
                    judge.loc[i,'final_Prod'] = get_dictproduct(Geodict, city)
                    judge.loc[i,'final_label'] = 2
                elif province in list(Geodict.values()):
                    judge.loc[i,'final_Prod'] = get_dictproduct(Geodict, province)
                    judge.loc[i,'final_label'] = 2
                else:
                    judge.loc[i,'final_label'] = -1  # -1表示存在多个可选项，但是都不够精确，因此只能人工筛选


        # 存在非地理标志产品就以地理标志产品为最终结果
        elif judge.NotGeoProdlist[i] is not None:
            province, city = get_Geodetail(judge, i)  # 获取省份、城市信息
            NotGeodict = judge.NotGeoProdlist[i]

            if len(NotGeodict) == 1:  # 只有一个字典，则默认为是准确值
                judge.loc[i,'final_Prod'] = list(NotGeodict.keys())[0]
                judge.loc[i,'final_label'] = 3
            else:
                if city in list(NotGeodict.values()):
                    judge.loc[i,'final_Prod'] = get_dictproduct(NotGeodict, city)
                    judge.loc[i,'final_label'] = 3
                elif province in list(NotGeodict.values()):
                    judge.loc[i,'final_Prod'] = get_dictproduct(NotGeodict, province)
                    judge.loc[i,'final_label'] = 3
                else:
                    judge.loc[i,'final_label'] = -1  # -1表示存在多个可选项，但是都不够精确，因此只能人工筛选


judge = judge[:5]

import time

time_start = time.time()  # 开始计时

get_SpecialProd(judge)
print('第一步完成')
get_GeoProd(judge)
print('第二步完成')
get_NotGeoProd(judge)
print('第三步完成')
final_Prod(judge)
print('全部完成')

judge.to_csv(r"C:\Users\sunsharp\Desktop\吴枭\区域公共品牌\2019.10\结果输出\结果.csv")

time_end = time.time()  # 结束计时
time_c = time_end - time_start  # 运行所花时间
print('time cost', time_c, 's')
