# -*- coding: utf-8 -*-
"""
Created on Sat Nov 23 19:40:02 2019

@author: wanggor
"""


from utils import preprocessing, geopath
from models import logistic_models as ls
import random
            
def random_route(data,original):
    output = [original]
    for i in data:
        for j in data[i]:
            if j not in output:
                output.append(j)
    output.remove(original)
    random.shuffle(output)
    return data, [original]+output
    
path1 ="data/Data.xlsx"
path2 ="data/Data Ship.xlsx"
path = [path1,path2]

data = preprocessing.parsing_data_2(path)
pelabuhan = ls.JaringanPelabuhan()

pelabuhan.add_multiPelabuhan(data["Daftar Pelabuhan"])
pelabuhan.add_rute_from_lis(data["Rute"])

pelabuhan.add_barang(data["Barang"])
pelabuhan.add_transit(data)
Total_Nilai_Harga, data["Barang"] = pelabuhan.add_Harga(data["Harga Barang"], data["Daftar Pelabuhan"], data["Barang"])


object_kapal = [ls.Kapal(pelabuhan, kpl["nama"], kpl["kategori"], kpl["kapasitas"], kpl["rute"], kpl["speed"],kpl) for kpl in data["Kapal"]]

        
original_port = { i["nama"]: [i["kategori"],i["rute"][0]] for i in data["Kapal"]}
data_kode_barang = pelabuhan.get_rute_barang(data["port"],original_port, data["Daftar Pelabuhan"])

for kpl in object_kapal:
    original_port = kpl.rute_name[0]
    if kpl.kategori in ["TL", "PL"]:
          kpl.add_rute(pelabuhan,random_route(data_kode_barang["Jarak Jauh"],original_port))
    else:
          kpl.add_rute(pelabuhan,random_route(data_kode_barang["Jarak Dekat"],original_port))
        
n = 0 
sisa = 1
while True:
    n += 1
    [i.update(pelabuhan) for i in object_kapal]
    pelabuhan.checking_posisi(object_kapal)
    
    cost = sum([float(i.get_data()["Total"]) for i in object_kapal])
    total = Total_Nilai_Harga

    sisa = sum([ float(i["Total"]) for i in pelabuhan.get_barang()])
    revenue = sum([ float(i["Bobot"]) for i in pelabuhan.get_barang_sampai()])
    beban_kapal = sum([ float(i.beban_angkut) for i in object_kapal])
    transit = sum([ float(i["Total"]) for i in pelabuhan.get_barang_transit()])
    print(f"""
          ================
          Total     : {total}
          Sisa      : {sisa}
          Beban     : {beban_kapal}
          Sampai    : {revenue}
          Transit   : {transit}
          Cost : {cost}
          Itteration = {n}
          ================
          """)
    
    if (beban_kapal <= 0) and (sisa <= 0) and (transit <= 0):
        break
    
