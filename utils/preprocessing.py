# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 21:53:26 2019

@author: wanggor
"""

import pandas as pd
from collections import OrderedDict
from utils.training_utils import parse_dms
import numpy as np

def parsing_data(path):
    excel = pd.ExcelFile(path)
    data = {}
    for sheet_name in excel.sheet_names:
        data[sheet_name] = excel.parse(sheet_name)
        
    data['Daftar Pelabuhan'] = data['Daftar Pelabuhan'].to_dict("Report")
    data['Rute'] = data['Rute'].to_dict("Report")

    a = OrderedDict()
    name = None
    for i in data['Rute']: 
        if type(i['Pelabuhan Asal']) == str:
            name = (i['Pelabuhan Asal'],i['Pelabuhan Tujuan'])
            a[name] =[]
        a[name].append([i['LATITUDE'],i['LONGITUDE']])
    
    data['Rute'] = a
    data['Barang'] = data['Barang'].to_dict("Report")
    return data

def parsing_data_2(path):
    data = {}
    pel = pd.read_excel(path[0], sheet_name ="port_loc")
    port = pd.read_excel(path[0], sheet_name ="ports")
    port = port.set_index("port")
    data["port"] = port.to_dict()["port_type"]

    pel["Latitude"] = pel["Latitude"].apply(parse_dms)
    pel["Longitude"] = pel["Longitude"].apply(parse_dms)
    pel["Tipe"] = pel["Nama Pelabuhan"].map(port["port_type"])
    
    data["Daftar Pelabuhan"]  = pel.dropna().to_dict("Report")
    
#    data["Pelabuhan Pengumpul"] = pel[pel["Tipe"] == "P"].to_dict("Report")
    
    data['Rute'] = pd.read_excel(path[0], sheet_name ="Rute").to_dict("Report")
    
    data["Barang"] = pd.read_excel(path[0], sheet_name ="Barang").to_dict("Report")
    
    data["Harga Barang"] = pd.read_excel(path[0], sheet_name ="Biaya_Jarak_Teus")
    data["Harga Barang"] = data["Harga Barang"].applymap(lambda x: x.strip() if isinstance(x, str) else x)
    data["Harga Barang"] = data["Harga Barang"].fillna(data["Harga Barang"].mean().mean()).set_index("Unnamed: 0")

    a = OrderedDict()
    name = None
    for i in data['Rute']: 
        if type(i['Pelabuhan Asal']) == str:
            name = (i['Pelabuhan Asal'],i['Pelabuhan Tujuan'])
            a[name] =[]
        a[name].append([parse_dms(i['LATITUDE']),parse_dms(i['LONGITUDE'])])
    
    data['Rute'] = a
    print(data['Rute'])
    dataTL =pd.read_excel(path[0], sheet_name="TL_char", index_col = "Unnamed: 0").fillna(3).to_dict()
    dataPL =pd.read_excel(path[0], sheet_name="PL_char", index_col = "Unnamed: 0").fillna(3).to_dict()
    dataPR =pd.read_excel(path[0], sheet_name="PR_char", index_col = "Unnamed: 0").fillna(3).to_dict()
     
    data['Kapal'] = []
    exel = pd.ExcelFile(path[1])
    for name in exel.sheet_names:
        ex = exel.parse(sheet_name=name)
        
        if ex.iloc[0,1] == "TL":
            capacity = dataTL["ship_char"]['VC']
            speed =  dataTL["ship_char"]['V']
            max_voyage = dataTL["ship_char"]['max_voyage']
            bm_time = {i:dataTL[i]["bm_time"] for i in dataTL.keys()}
            avg_docking_time = {i:dataTL[i]["avg_docking_time"] for i in dataTL.keys()}
            port_storage_time = {i:dataTL[i]["port_storage_time"] for i in dataTL.keys()}
            C_bm = {i:dataTL[i]["C_bm"] for i in dataTL.keys()}
            C_storage = {i:dataTL[i]["C_storage"] for i in dataTL.keys()}
            inventory_cost = {i:dataTL[i]["inventory_cost"] for i in dataTL.keys()}
        
        elif ex.iloc[0,1] == "PL":
            capacity = dataPL["ship_char"]['VC']
            speed =  dataPL["ship_char"]['V']
            max_voyage = dataPL["ship_char"]['max_voyage']
            bm_time = {i:dataPL[i]["bm_time"] for i in dataPL.keys()}
            avg_docking_time = {i:dataPL[i]["avg_docking_time"] for i in dataPL.keys()}
            port_storage_time = {i:dataPL[i]["port_storage_time"] for i in dataPL.keys()}
            C_bm = {i:dataPL[i]["C_bm"] for i in dataPL.keys()}
            C_storage = {i:dataPL[i]["C_storage"] for i in dataPL.keys()}
            inventory_cost = {i:dataPL[i]["inventory_cost"] for i in dataPL.keys()}
            
        elif ex.iloc[0,1] == "PR":
            capacity = dataPR["ship_char"]['VC']
            speed =  dataPR["ship_char"]['V']
            max_voyage = dataPR["ship_char"]['max_voyage']
            bm_time = {i:dataPR[i]["bm_time"] for i in dataPR.keys()}
            avg_docking_time = {i:dataPR[i]["avg_docking_time"] for i in dataPR.keys()}
            port_storage_time = {i:dataPR[i]["port_storage_time"] for i in dataPR.keys()}
            C_bm = {i:dataPR[i]["C_bm"] for i in dataPR.keys()}
            C_storage = {i:dataPR[i]["C_storage"] for i in dataPR.keys()}
            inventory_cost = {i:dataPR[i]["inventory_cost"] for i in dataPR.keys()}
        
        data['Kapal'].append(
                {
                        "nama":name,
                        "kategori": ex.iloc[0,1],
                        "kapasitas": capacity,
                        "rute": list(ex.iloc[:,2].values),
                        "speed": speed,
                        "bm_time" :bm_time,
                        "avg_docking_time": avg_docking_time,
                        "port_storage_time" : port_storage_time,
                        "C_bm": C_bm,
                        "C_storage": C_storage, 
                        "inventory_cost" : inventory_cost,
                        "max_voyage" :max_voyage
                        }
                )
    data['Wave'] = pd.read_excel(path[0], sheet_name ="wave_status").applymap(lambda x: x.strip() if isinstance(x, str) else x).to_dict("Report")

    spesial_pr = pd.read_excel(path[0], sheet_name = "special_PR", index = None).applymap(lambda x: x.strip() if isinstance(x, str) else x).to_dict("list")
    data["Spesial PR"] = {}
    for key, val in spesial_pr.items():
        data["Spesial PR"][key]  = [ v for v in val if not isnan(v)]
    return data

def isnan(value):
    try:
        import math
        return math.isnan(float(value))
    except:
        return False
    