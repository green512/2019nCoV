# -*- coding: utf-8 -*-

import csv
import json
import requests
import time  # 引入time模块
import datetime
import schedule


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
    main()
    #清空任务
    schedule.clear()
    #创建一个按秒间隔执行任务
    schedule.every(30).minutes.do(main)   
    while True:
        schedule.run_pending()