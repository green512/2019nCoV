# -*- coding: utf-8 -*-

import re
import csv
import json
import requests
import time  # 引入time模块
import datetime
import schedule
from urllib.request import Request


def load_amap_cities():
    return dict([line.strip().split() for line in open('adcodes', encoding='utf8').readlines()])


amap_code_to_city = load_amap_cities()
#print(amap_code_to_city)
amap_city_to_code = {v: k for k, v in amap_code_to_city.items()}
city_list=[v for k, v in amap_code_to_city.items()]
amap_short_city_to_full_city = {k[0:2]: k for k in amap_city_to_code}

def normalize_city_name(dxy_province_name, dxy_city_name):
    # 忽略部分内容
    ignore_list = ['外地来京人员', '未知']
    if dxy_city_name in ignore_list:
        return ''
    if len(dxy_city_name)<1:
       return '' 

    # 手动映射
    # 高德地图里没有两江新区，姑且算入渝北
    manual_mapping = {'巩义': '郑州市', '满洲里': '呼伦贝尔市', '固始县': '信阳市', '阿拉善': '阿拉善盟','两江新区':'渝北区',
                      '第七师': '塔城地区', '第八师石河子': '石河子市'}
    if manual_mapping.get(dxy_city_name):
        return manual_mapping[dxy_city_name]

    # 名称规则
    # 例如 临高县 其实是市级
    if dxy_city_name[-1] in ['市', '县', '盟']:
        normalized_name = dxy_city_name
    elif dxy_province_name == '重庆市' and dxy_city_name[-1] == '区':
        normalized_name = dxy_city_name
    elif dxy_province_name == '北京':
        normalized_name = dxy_city_name 
        if dxy_city_name[-1] != '区': normalized_name = dxy_city_name + '区'
        return normalized_name
        #print(normalized_name)
    else:
        normalized_name = dxy_city_name + '市'
    if normalized_name in amap_city_to_code:
        return normalized_name

    # 前缀匹配
    # adcodes 里面的规范市名，出了 张家口市/张家界市，阿拉善盟/阿拉尔市 外，前两个字都是唯一的
    # cat adcodes|cut -d' ' -f2|cut -c1-2|sort|uniq -c |sort -k2n
    # 所以可以用前两个字
    normalized_name = amap_short_city_to_full_city.get(dxy_city_name[0:2], '')
    #if normalized_name != dxy_city_name:
    #  print('fuzz map', dxy_province_name, dxy_city_name, 'to', normalized_name)
    return normalized_name

def load_dxy_data1():
    url = 'https://3g.dxy.cn/newh5/view/pneumonia?&_=%d'%int(time.time()*1000)
    raw_html = requests.get(url).content.decode('utf8')
    match = re.search('window.getListByCountryTypeService1 = (.*?)}catch', raw_html)
    raw_json = match.group(1)
    result = json.loads(raw_json, encoding='utf8')
    return result

def load_dxy_data2():
    url = 'https://3g.dxy.cn/newh5/view/pneumonia?&_=%d'%int(time.time()*1000)
    print(url)
    raw_html = requests.get(url).content.decode('utf8')
    match = re.search('window.getListByCountryTypeService2 = (.*?)}catch', raw_html)
    raw_json = match.group(1)
    result = json.loads(raw_json, encoding='utf8')
    return result

def write_world(result1,result2):
    writer = open('confirmed_world.js', 'w', encoding='utf8')
    writer.write('const LAST_UPDATE = "')
    writer.write(datetime.datetime.now(datetime.timezone(
        datetime.timedelta(hours=8))).strftime('%Y%m%d-%H:%M:%S'))
    writer.write('"; \r\n')
    writer.write("const province = ")
    json.dump(result1, writer, indent='  ', ensure_ascii=False)
    writer.write('; \r\n')
    writer.write("const world = ")
    json.dump(result2, writer, indent='  ', ensure_ascii=False)
    writer.write('; \r\n')
    writer.close()

def load_dxy_data():
    result1=load_dxy_data1()
    result2=load_dxy_data2()
    write_world(result1,result2)

    
def load_qq_data():
    date_list=list()
    confirm_list=list()
    suspect_list=list()
    dead_list=list()
    heal_list=list()
    date_list_=list()
    confirm_list_=list()
    suspect_list_=list()
    dead_list_=list()
    heal_list_=list()
    url = 'https://view.inews.qq.com/g2/getOnsInfo?name=disease_h5&callback=&_=%d'%int(time.time()*1000)
    result=json.loads(requests.get(url=url).json()['data'])
    for item in result['chinaDayList']:
        date_list.append(item['date'])
        confirm_list.append(item['confirm'])
        suspect_list.append(item['suspect'])
        dead_list.append(item['dead'])
        heal_list.append(item['heal'])
    for item in result['chinaDayAddList']:
        date_list_.append(item['date'])
        confirm_list_.append(item['confirm'])
        suspect_list_.append(item['suspect'])
        dead_list_.append(item['dead'])
        heal_list_.append(item['heal'])
    writer = open('2019nCov_data.js', 'w', encoding='utf8')
    writer.write('const LAST_UPDATE = "')
    writer.write(datetime.datetime.now(datetime.timezone(
        datetime.timedelta(hours=8))).strftime('%Y.%m.%d-%H:%M:%S'))
    writer.write('"; \r\n')
    
    date_str=['date_list']+date_list
    confirm_str=['确诊']+confirm_list
    suspect_str=['疑似']+suspect_list
    dead_str=['死亡']+dead_list
    heal_str=['治愈']+heal_list
    print(str(date_str))    
    writer.write("const DATA_2019 = [")
    writer.write(str(date_str)+", \n") 
    writer.write(str(confirm_str)+", \n") 
    writer.write(str(suspect_str)+", \n") 
    writer.write(str(dead_str)+", \n") 
    writer.write(str(heal_str)) 
    writer.write("]; \n")   

    date_str=['date_list']+date_list_
    confirm_str=['新增确诊']+confirm_list_
    suspect_str=['新增疑似']+suspect_list_
    dead_str=['新增死亡']+dead_list_
    heal_str=['新增治愈']+heal_list_
    print(str(date_str))    
    writer.write("const DATA_ADD = [")
    writer.write(str(date_str)+", \n") 
    writer.write(str(confirm_str)+", \n") 
    writer.write(str(suspect_str)+", \n") 
    writer.write(str(dead_str)+", \n") 
    writer.write(str(heal_str)) 
    writer.write("]; \n")   
    writer.close()
    url = 'https://ncov.html5.qq.com/api/getCommunity'
    result=requests.get(url=url).json()['community']
    print(list(result.keys()))
    writer = open('confirmed_places.js', 'w', encoding='utf8')
    writer.write('const LAST_UPDATE = "')
    writer.write(datetime.datetime.now(datetime.timezone(
        datetime.timedelta(hours=8))).strftime('%Y.%m.%d-%H:%M:%S'))
    writer.write('"; \r\n')
    writer.write("const PLACES = [")
    for key in list(result.keys()) :
        if key in ['北京市', '上海市', '天津市', '重庆市']:
            writer.write(str(result[key])+", \n")     
    writer.write("]; \n") 
    writer.close()
    



def write_result(result):
    writer = open('confirmed_datas.js', 'w', encoding='utf8')
    writer.write('const LAST_UPDATE = "')
    writer.write(datetime.datetime.now(datetime.timezone(
        datetime.timedelta(hours=8))).strftime('%Y%m%d-%H:%M:%S'))
    writer.write('"; \r\n')
    writer.write("const DATAS = ")
    json.dump(result, writer, indent='  ', ensure_ascii=False)
    writer.close()

# 获取列表的第二个元素
def takeSecond(elem):
    return elem[1]

def main():

    date_list = list() # 日期
    data_list=list()
    url = 'http://datanews.caixin.com/interactive/2020/iframe/pneumonia-new/data/pneumonia.csv'
    url = 'http://datanews.caixin.com/interactive/2020/pneumonia-h5/data/pneumonia.csv'
    u_csv = requests.get(url).content.decode('utf8')
    writer = open('pneumonia.csv', 'w', encoding='utf8')
    writer.write(u_csv)
    writer.close()
    writer = open('2019pneumonia.csv', 'w', encoding='utf8')
    with open('pneumonia.csv' , encoding='utf8')as f:
        f_csv = csv.reader(f)
        #print(f_csv[0][1])
        for row in f_csv:
            if row[2] != '省份':
                row[3]=normalize_city_name(row[2],row[3])
                date_list.append(row[1])
                data_list.append(row)
            writer.write(', '.join(row)+'\n')
    #date_list.sort()        
    #print(date_list[len(date_list)-1])
    #print(max(date_list)-min(date_list))
    writer.close()
    syear,smonth, sday = min(date_list).split('/')         
    eyear,emonth, eday = max(date_list).split('/') 
    sdate =datetime.date(int(syear),int(smonth), int(sday))
    sdate =datetime.date(2020,1,15)
    edate =datetime.date(int(eyear),int(emonth), int(eday))
    print(edate-sdate)
    date_list.clear()
    for i in range((edate-sdate).days+1):
        date_list.append(sdate+datetime.timedelta(days=i))
    #print(date_list)

    data_list.sort(key=takeSecond, reverse=True)

    result = {}
    writer = open('2019pneumonias.csv', 'w', encoding='utf8')
    for d in date_list:
        d0 = d-datetime.timedelta(days=1)
        date0='%d/%d/%d' % (d0.year,d0.month,d0.day)
        
        date1='%d/%d/%d' % (d.year,d.month,d.day)
        #print(date)
        clist=list()
        #for c in city_list:
        #print(c)

        for row in data_list:
            confirmedCount =0
            cityname=""        
            #print(row[3] , c)
            #if (c in row[3]) : confirmedCount=row[4]            
            #if ((date1 == row[1].strip(" ")) and (c in row[3])):
            if ((date1 == row[1].strip(" "))):                                 
                confirmedCount = row[4]
                cityname = row[3].strip(" ")
                #print(date1,cityname,confirmedCount)
                writer.write('%s,%s,%s \n' % (date1,cityname,confirmedCount))            
                if(cityname !=""):
                    clist.append([cityname,confirmedCount])
        if(d0>sdate):
            #print(date1,len(result[date0]),len(clist))
            if len(clist) ==0:
                for kk in result[date0] :
                    clist.append([kk['cname'],kk['confirmCount']])
                result[date1] = [{'cname':k,'confirmCount':v}  for k, v in clist]
                continue
            cs=list()
            for kv in clist:
                cs.append(kv[0])
            for k in result[date0] :    
                if not(k['cname'] in cs) : 
                    clist.append([k['cname'],k['confirmCount']])
                    

        result[date1] = [{'cname':k,'confirmCount':v}  for k, v in clist]
    write_result(result)
    writer.close()


if __name__ == '__main__':
    load_qq_data()
    main()
    load_dxy_data()
    #清空任务
    schedule.clear()
    # #创建一个按秒间隔执行任务
    schedule.every(2).hours.do(main) 
    schedule.every(30).minutes.do(load_dxy_data)  
    schedule.every(30).minutes.do(load_qq_data)
    while True:
        schedule.run_pending()
