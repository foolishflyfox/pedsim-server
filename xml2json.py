import os.path
import xml.dom.minidom
import json
import random
from flask import render_template

from utils import GetLosseMaxRect, MaxRectBound

# 将一个 subroom 解析成一个 FuncArea 对象
# subroom 是一个 xml.dom.minidom.Element 类型
def parseSubroom(subroom):
    s_subroom_id = subroom.getAttribute('id')
    polygons = subroom.getElementsByTagName('polygon')
    sub_funcareas = []
    for polygon in polygons:
        t_caption = polygon.getAttribute('caption')
        sub_funcarea = {}
        if(s_subroom_id):
            sub_funcarea['_id'] = int(s_subroom_id)
        sub_funcarea['Wall'] = 'subroom'
        sub_funcarea['Open'] = True
        sub_funcarea['Outline'] = [[]]
        points = []
        vertexs = polygon.getElementsByTagName('vertex')
        for vertex in vertexs:
            points.append(float(vertex.getAttribute('px')))
            points.append(float(vertex.getAttribute('py')))
        sub_funcarea['Outline'][0].append(points)
        sub_funcareas.append(sub_funcarea)
    return sub_funcareas

# 求FuncAreas的外边界
def GetFloorOutline(FuncAreas):
    dots = []
    for FuncArea in FuncAreas:
        # print("funcarea :", FuncArea['Outline'][0][0])
        # print('aaaa:', FuncArea['Outline'][0][0])
        i = 0
        t_outline = FuncArea['Outline'][0][0]
        while i < len(t_outline):
            dots.append((int(t_outline[i]), int(t_outline[i+1])))
            i += 2
    # print('t0 ',len(dots))
    # print(dots)
    # result = graham_scan(dots)
    result = GetLosseMaxRect(dots)

    return result

# 构建 Floor 对象
def CreateFloor(FuncAreas):
    Floor = {"_id":1, "Name":"F1", "High":5, "FuncAreas":[],
        "PubPoint":[]}
    # print(FuncAreas)
    for FuncArea in FuncAreas:
        Floor['FuncAreas'].append(FuncArea)
    Floor['Outline'] = [[GetFloorOutline(Floor['FuncAreas'])]]
    return Floor

# TODO: 构建 Building 对象
def CreateBuilding(Floors):
    building = {"Outline":[[[]]]}
    return building

def CreateMapJsonFile(geoxml_path, geojson_path):
    result = {'data':{'Floors':[]}}
    Floors = result['data']['Floors']

    dom = xml.dom.minidom.parse(geoxml_path)
    geometry = dom.documentElement
    # 一个 map 只能有一个rooms
    rooms = geometry.getElementsByTagName('rooms')[0]
    room_list = rooms.getElementsByTagName('room')
    
    FuncAreas = []
    for room in room_list:
        subrooms = room.getElementsByTagName('subroom')
        for subroom in subrooms:
            sub_funcareas = parseSubroom(subroom)
            FuncAreas += sub_funcareas

    Floor = CreateFloor(FuncAreas)
    
    # 调整位置和大小的参数，使显示的场景更加适合界面
    t_left = MaxRectBound(Floor['Outline'][0][0], 'left')
    t_right = MaxRectBound(Floor['Outline'][0][0], 'right')
    t_bottom = MaxRectBound(Floor['Outline'][0][0], 'bottom')
    t_top = MaxRectBound(Floor['Outline'][0][0], 'top')
    xcenter = (t_left+t_right)/2
    ycenter = (t_bottom+t_top)/2
    xlen = (t_right-t_left)
    ylen = (t_top-t_bottom)
    mlen = max(xlen, ylen)
    scale = 1500/mlen
    outline = Floor['Outline'][0][0]
    for i in range(len(outline)):
        if i%2: 
            outline[i] = (outline[i]-ycenter)*scale
        else: 
            outline[i] = (outline[i]-xcenter)*scale
    for i in range(len(Floor['FuncAreas'])):
        j = 0
        outline = Floor['FuncAreas'][i]['Outline'][0][0]
        while j+1 < len(outline):
            outline[j] = (outline[j]-xcenter)*scale
            outline[j+1] = (outline[j+1]-ycenter)*scale
            j += 2
    # print(Floor)
    # 调整 Floor 的 High 属性以改变墙的高度
    Floor['High'] = min(xlen, ylen)*scale/50
    Floors.append(Floor)
    result['data']['building'] = CreateBuilding(Floors)
    # print(json.dumps(result, indent=2))
    with open(geojson_path, 'w') as output:
        json.dump(result, output, indent=2)
    

def map_xml2json(simname, showtype=True):
    simdir = f"./simulations/{simname}"
    inipath = f"{simdir}/ini.xml"
    dom = xml.dom.minidom.parse(inipath)
    root = dom.documentElement
    geometry = root.getElementsByTagName('geometry')[0]
    geoname_xml = geometry.firstChild.data
    geoname_json = os.path.splitext(geoname_xml)[0]+'.json'
    geoxml_path = f"{simdir}/{geoname_xml}"
    geojson_path = f"{simdir}/{geoname_json}"
    if(not os.path.isfile(geojson_path)):
        CreateMapJsonFile(geoxml_path, geojson_path)
    return render_template('./simulate.html', datafile=geojson_path, showtype=showtype)
    
    


