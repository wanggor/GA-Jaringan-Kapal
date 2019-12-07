# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 17:09:19 2019

@author: wanggor
"""
from pyqtlet import L
from utils import geopath
from datetime import timedelta
import random

def cost(data, jarak ):
    return data

class Pelabuhan():
    def __init__(self, nama, kategori, posisi):
        self.nama = nama
        self.kategori = kategori
        self.posisi = posisi
        self.is_high = False
        self.barang = []
        self.barang_sampai = {}
        self.barang_transit = {}
        self.Total_Nominal = 0
        
    def reset(self):
        self.barang = []
        self.barang_sampai = {}
        self.barang_transit = {}
        self.Total_Nominal = 0
    
    def angkut_barang(self,kapasitas_kapal):
        barang_angkut = []
        total = 0
        delete = []
        for n,brg in enumerate(self.barang):
            total += brg["beban"]
            if total <= kapasitas_kapal:
                barang_angkut.append(brg)
                delete.append(n)
            else:
                sisa = total - kapasitas_kapal
                if sisa <= 0 :
                    break
                else:
                    self.barang[n]["beban"] = self.barang[n]["beban"]-sisa
                    barang_angkut.append({
                                "nama" : brg["nama"],
                                "tujuan" : brg["tujuan"],
                                "beban" : sisa
                            })
        self.barang = [j for i, j in enumerate(self.barang) if i not in delete]
        return barang_angkut
    
    
class JaringanPelabuhan():
    def __init__(self):
        self.lis_pelabuhan = {}
        self.rute = {}        
        self.marker = {}
        self.pel_cuaca_tinggi = []
        
    def add_pelabuhan(self, nama, kategori, posisi):    
        self.lis_pelabuhan[nama] = Pelabuhan(nama, kategori, posisi)                
        for pel, item in self.lis_pelabuhan.items():
            self.rute[(nama,pel)] = [posisi,item.posisi]
                
    def add_multiPelabuhan(self, data):
        for item in data:
            self.add_pelabuhan(item["Nama Pelabuhan"], item["Tipe"], [item["Latitude"],item["Longitude"]])
            
    def get_full_path(self,distance,  rute = []):
        output_path = []
        for n, name in enumerate(rute):
            awal = name
            output_path.append({})
            if n < len(rute)-1:
                akhir = rute[n+1]
            else:
                akhir = rute[0]
            output_path[-1]["nama"] = awal+' - '+akhir
            output_path[-1]["rute"] = []
            path_a = []
            if (awal,akhir) in self.rute.keys():
                for i in self.rute[(awal,akhir)]:
                    path_a.append(i)
            elif (akhir,awal) in self.rute.keys():
                path = self.rute[(akhir,awal)].copy()
                path.reverse()              
                for i in path:
                    path_a.append(i)
            for n in range(len(path_a)):
                if n < len(path_a)-1:
                    azimuth = geopath.calculateBearing(path_a[n][0],path_a[n][1],path_a[n+1][0],path_a[n+1][1])
                    result = geopath.main(distance,azimuth,path_a[n][0],path_a[n][1],path_a[n+1][0],path_a[n+1][1])
                    for i in result[:-1]:
                        output_path[-1]["rute"].append(i)
        return output_path
    
    def add_rute_from_lis(self,data):
        rute = list(self.rute.keys())
        for key in data:
            a = key
            b = (key[-1],key[0])
            
            if a in rute:
                self.rute[a] = data[key]
            elif b in rute:
                c = data[key].copy()
                c.reverse()
                self.rute[b] = c
        
    def add_rute(self, awal, tujuan, rute = []):
        for nama in self.rute:
            if (awal in nama) and  (tujuan in nama):
                rute.insert(0, self.rute[nama][0])
                rute.append(self.rute[nama][1])
                self.rute[nama] = rute
                break
    
    def draw(self,map_obj, track = False, data_kategori = None, color_picker= None):
        if track :
            poly = [i for i in self.rute.values()]
            if poly:
                map_obj.addLayer(L.polyline(poly, options= "{color : '#b5b8bd'}"))

        for name,pel in self.lis_pelabuhan.items():
            for n,i in enumerate(data_kategori):
                if name in data_kategori[i]:
                    break

            options = None
            if pel.kategori.lower() == "p":
                options= "{color : '#0cb500', radius: 8}"
            elif  pel.kategori.lower() == "u":
                options= "{color : '#ff2617', radius: 8}"
            else:
                color = str(color_picker.get_hex(n))
                options= "{color : '"+color+"', radius: 4}"

                
            self.marker[name] = L.circleMarker(pel.posisi,options= options)
            self.marker[name].bindPopup(pel.nama.capitalize())
            map_obj.addLayer(self.marker[name])
            
    def add_barang(self, barang):
        for item in barang:
            biaya = item['Nilai Barang']
            self.lis_pelabuhan[item['Pelabuhan']].barang.append(
                    {
                            'Kode Barang': item['code barang'], 
                            "Tujuan Pelabuhan": item['Tujuan Pelabuhan'],
                            "Asal Pelabuhan" : item['Pelabuhan'],
                            "Bobot" : item['Bobot'],
                            "Total" : item['Bobot'],
                            "Biaya" : biaya,
                            })
            self.lis_pelabuhan[item['Pelabuhan']].Total_Nominal += biaya
            
    def add_transit_cluster(self, data):
        for name_pel,pel in self.lis_pelabuhan.items():
            if pel.kategori == "U":
                for brg in pel.barang:
                    tujuan = brg["Tujuan Pelabuhan"]
                    if (data["port"][tujuan]) == "R":
                        brg["Transit"] = self.get_minimum_distance_pel(tujuan, data, "P")
                    else:
                        brg["Transit"] = "None"   
            
            elif pel.kategori == "R":
                
                for brg in pel.barang:
                    tujuan = brg["Tujuan Pelabuhan"]
                    asal = brg["Asal Pelabuhan"]

                    kategori = None
                    for kategori_cluster in data["Spesial PR"]:
                        if asal in data["Spesial PR"][kategori_cluster]:
                            kategori = kategori_cluster
                            break

                    if (data["port"][tujuan]) == "U":
                        
                        brg["Transit"] = self.get_minimum_distance_pel(asal, data, "P")
                    
                    elif (tujuan not in data["Spesial PR"][kategori]) and (data["port"][tujuan]) == "R":
                        
                        brg["Transit"] = []
                        brg["Transit"].append(self.get_minimum_distance_pel(asal, data, "P"))
                        brg["Transit"].append(self.get_minimum_distance_pel(tujuan, data, "P"))

                    elif (tujuan not in data["Spesial PR"][kategori]) and (data["port"][tujuan]) == "P":
                        
                        brg["Transit"] = self.get_minimum_distance_pel(asal, data, "P")
                    else:
                        brg["Transit"] = "None"
            else:
                for brg in pel.barang:
                    tujuan = brg["Tujuan Pelabuhan"]
                    asal = brg["Asal Pelabuhan"]

                    kategori = None
                    for kategori_cluster in data["Spesial PR"]:
                        if asal in data["Spesial PR"][kategori_cluster]:
                            kategori = kategori_cluster
                            break

                    if (tujuan not in data["Spesial PR"][kategori]) and (data["port"][tujuan]) == "R":
                        brg["Transit"] = self.get_minimum_distance_pel(tujuan, data, "P")
                    else:
                        brg["Transit"] = "None"
            for brg in pel.barang:
                brg["track"] = ""
                if pel.kategori == "U":
                    brg["track"] += "U"
                else:
                    if pel.kategori == "R":
                        brg["track"] += "R"
                    elif pel.kategori == "P":
                        brg["track"] += "P"
                
                if type(brg["Transit"]) == list:
                    for i in brg["Transit"]:
                        brg["track"] += "-P"
                else:
                   if brg["Transit"] != "None":
                        brg["track"] += "-P"
                
                if data["port"][brg["Tujuan Pelabuhan"]] == "U":
                    brg["track"] += "-U"
                else:
                    kategori = None
                    if data["port"][brg["Tujuan Pelabuhan"]] == "R":
                        brg["track"] += "-R"
                    elif data["port"][brg["Tujuan Pelabuhan"]] == "P":
                        brg["track"] += "-P"
            

    def get_minimum_distance_pel(self, pel, data, kat = "P"):
        name = None
        d_min = None

        kategori = None
        for kategori_cluster in data["Spesial PR"]:
            if pel in data["Spesial PR"][kategori_cluster]:
                kategori = kategori_cluster
                break
        for pel_peng in [k for k in data["Spesial PR"][kategori] if data["port"][k] == kat]:
            if ( pel,pel_peng) in self.rute.keys():
                rute = self.rute[( pel,pel_peng)]
                d = sum([ geopath.getPathLength(rute[i][0],rute[i][1],rute[i+1][0],rute[i+1][1]) for i in range(len(rute)-1)])
                if d_min is None:
                    d_min = d
                    name = pel_peng
                if d< d_min:
                    name = pel_peng
 
            elif ( pel_peng,pel) in self.rute.keys():
                rute = self.rute[( pel_peng,pel)]
                d = sum([geopath.getPathLength(rute[i][0],rute[i][1],rute[i+1][0],rute[i+1][1]) for i in range(len(rute)-1)])
                if d_min is None:
                    d_min = d
                if d< d_min:
                    name = pel_peng
                d_min = min(d, d_min)
        return name

    def add_transit(self, data):
        for name_pel,pel in self.lis_pelabuhan.items():
            if pel.kategori == "U":
                for brg in pel.barang:
                    tujuan = brg["Tujuan Pelabuhan"]
                    if (data["port"][tujuan]) == "R":
                        name = None
                        d_min = None
                        for pel_peng in [k for k in data["port"] if data["port"][k] == "P"]:
                            if ( tujuan,pel_peng) in self.rute.keys():
                                rute = self.rute[( tujuan,pel_peng)]
                                d = sum([ geopath.getPathLength(rute[i][0],rute[i][1],rute[i+1][0],rute[i+1][1]) for i in range(len(rute)-1)])
                                if d_min is None:
                                    d_min = d
                                if d< d_min:
                                    name = pel_peng
                                d_min = min(d, d_min)
                            elif ( pel_peng,tujuan) in self.rute.keys():
                                rute = self.rute[( pel_peng,tujuan)]
                                d = sum([geopath.getPathLength(rute[i][0],rute[i][1],rute[i+1][0],rute[i+1][1]) for i in range(len(rute)-1)])
                                if d_min is None:
                                    d_min = d
                                if d< d_min:
                                    name = pel_peng
                                d_min = min(d, d_min)
                        brg["Transit"] = name
                    else:
                        brg["Transit"] = tujuan
            else:
                for brg in pel.barang:
                    tujuan = brg["Tujuan Pelabuhan"]
                    if (data["port"][tujuan]) == "U":
                        name = None
                        d_min = None
                        for pel_peng in [k for k in data["port"] if data["port"][k] == "P"]:
                            if ( tujuan,pel_peng) in self.rute.keys():
                                rute = self.rute[( tujuan,pel_peng)]
                                d = sum([ geopath.getPathLength(rute[i][0],rute[i][1],rute[i+1][0],rute[i+1][1]) for i in range(len(rute)-1)])
                                if d_min is None:
                                    d_min = d
                                if d< d_min:
                                    name = pel_peng
                                d_min = min(d, d_min)
                            elif ( pel_peng,tujuan) in self.rute.keys():
                                rute = self.rute[( pel_peng,tujuan)]
                                d = sum([geopath.getPathLength(rute[i][0],rute[i][1],rute[i+1][0],rute[i+1][1]) for i in range(len(rute)-1)])
                                if d_min is None:
                                    d_min = d
                                if d< d_min:
                                    name = pel_peng
                                d_min = min(d, d_min)
                        brg["Transit"] = name
                    else:
                        brg["Transit"] = "None"
    
    def get_barang(self):
        data = []
        for items in self.lis_pelabuhan.values():
            nama = items.nama
            sum_transit = sum([self.lis_pelabuhan[nama].barang_transit[i]["Bobot"] for i in self.lis_pelabuhan[nama].barang_transit])
            total = sum([item["Bobot"] for item in items.barang])
            total_Nominal = items.Total_Nominal
            kondisi = items.is_high
            data.append({
                    "Pelabuhan" : nama,
                    "Total" : total,
                    "Transit" : sum_transit, 
                    "Kondisi": kondisi,
                    "Total Nominal": total_Nominal})
    
        return data
  
    def add_Harga(self, data, pelabuhan, data_barang):
        harga = 0
        for pel in self.lis_pelabuhan:
              barang = self.lis_pelabuhan[pel].barang
              for n, brg in enumerate(barang):
                    condition = False
                    if type(brg["Transit"]) != list:
                        condition =  brg["Tujuan Pelabuhan"] != brg["Transit"] and brg["Transit"] != "None"
                    else:
                        condition =  (brg["Tujuan Pelabuhan"] != brg["Transit"][0] or brg["Tujuan Pelabuhan"] != brg["Transit"][1])  and brg["Transit"] != "None"
                    
                    if condition:
                        asal = brg["Asal Pelabuhan"]
                        poss_asal =  [[i["Latitude"], i["Longitude"]] for i in pelabuhan if i["Nama Pelabuhan"] == asal][0]
                        tujuan = brg["Tujuan Pelabuhan"]
                        poss_tujuan =  [[i["Latitude"], i["Longitude"]] for i in pelabuhan if i["Nama Pelabuhan"] == tujuan][0]
                        transit = brg["Transit"]
                        if type(transit) != list:
                            poss_transit =  [[i["Latitude"], i["Longitude"]] for i in pelabuhan if i["Nama Pelabuhan"] == transit][0]
                            jarak_tran = geopath.getPathLength(poss_asal[0],poss_asal[1],poss_transit[0],poss_transit[1])/1000
                        else:
                            poss_transit =  [[i["Latitude"], i["Longitude"]] for i in pelabuhan if i["Nama Pelabuhan"] == transit[0]][0]
                            jarak_tran = geopath.getPathLength(poss_asal[0],poss_asal[1],poss_transit[0],poss_transit[1])/1000
                            poss_transit2 =  [[i["Latitude"], i["Longitude"]] for i in pelabuhan if i["Nama Pelabuhan"] == transit[1]][0]
                            jarak_tran += geopath.getPathLength(poss_transit[0],poss_transit[1],poss_transit2[0],poss_transit2[1])/1000
                            jarak_tran += geopath.getPathLength(poss_transit2[0],poss_transit2[1],poss_tujuan[0],poss_tujuan[1])/1000

                        cont = data[asal][tujuan]
                        bobot = brg["Bobot"]
                        
                        jarak_tujuan = geopath.getPathLength(poss_transit[0],poss_transit[1],poss_tujuan[0],poss_tujuan[1])/1000
                        self.lis_pelabuhan[pel].barang[n]["Biaya"] = cont*bobot*(jarak_tran)
                        harga +=  cont*bobot*(jarak_tran)
                        
                        for n, i in enumerate(data_barang):
                            if i["code barang"] ==  brg["Kode Barang"]:
                                data_barang[n]["Nilai Barang"] = cont*bobot*(jarak_tran)
                  
                    else:
                          asal = brg["Asal Pelabuhan"]
                          poss_asal =  [[i["Latitude"], i["Longitude"]] for i in pelabuhan if i["Nama Pelabuhan"] == asal][0]
                          tujuan = brg["Tujuan Pelabuhan"]
                          poss_tujuan =  [[i["Latitude"], i["Longitude"]] for i in pelabuhan if i["Nama Pelabuhan"] == tujuan][0]
                          
                          cont = data[asal][tujuan]
                          bobot = brg["Bobot"]
                          jarak_tran = geopath.getPathLength(poss_asal[0],poss_asal[1],poss_tujuan[0],poss_tujuan[1])/1000
                          self.lis_pelabuhan[pel].barang[n]["Biaya"] = cont*bobot*(jarak_tran)
                          harga +=  cont*bobot*(jarak_tran)

                          for n, i in enumerate(data_barang):
                                if i["code barang"] ==  brg["Kode Barang"]:
                                      data_barang[n]["Nilai Barang"] = cont*bobot*(jarak_tran)                        
        return harga,data_barang
                          
                         
    
    
    def get_rute_barang(self, port, original_port, full_port):
        data_kode_barang = {}
        data_kode_barang["Jarak Jauh"] = {}
        data_kode_barang["Jarak Dekat"] = {}
        for items in self.lis_pelabuhan.values():
            for brg in items.barang:
                asal = brg["Asal Pelabuhan"]
                transit = brg["Transit"]
                
                if type(transit) != list:
                    transit = [transit]
                tujuan = brg["Tujuan Pelabuhan"]
                if (port[asal] == "U") :
                    data_kode_barang["Jarak Jauh"][brg["Kode Barang"]] = [asal]+transit
                    data_kode_barang["Jarak Dekat"][brg["Kode Barang"]] = transit+[tujuan]
                    
                elif(port[tujuan] == "U" and port[asal] != "U"):
                    data_kode_barang["Jarak Jauh"][brg["Kode Barang"]] = transit+[tujuan]
                    data_kode_barang["Jarak Dekat"][brg["Kode Barang"]] = [asal]+transit
                
                elif(port[tujuan] == "P" and port[asal] == "R"):
                    data_kode_barang["Jarak Jauh"][brg["Kode Barang"]] = transit+[tujuan]
                else:                    
                    if transit is not "None":
                        data_kode_barang["Jarak Dekat"][brg["Kode Barang"]] = [asal]+transit+[tujuan]
                    else:
                        data_kode_barang["Jarak Dekat"][brg["Kode Barang"]] = [asal,tujuan]
                # transit_utama = [i for i in transit if port[i] == "P"]
                transit_utama = []
                for i in transit:
                    if i != "None":
                        if port[i] == "P":
                            transit_utama.append(i)
                if transit_utama:
                    if port[tujuan] == "U":
                        data_kode_barang["Jarak Jauh"][brg["Kode Barang"]] = transit+[tujuan]
                    elif port[tujuan] == "P":
                        data_kode_barang["Jarak Jauh"][brg["Kode Barang"]] = transit+[tujuan]
                    else:
                        data_kode_barang["Jarak Jauh"][brg["Kode Barang"]] = transit
        return data_kode_barang
    
    def find_closest(self, data, v):
        return min(data, key = lambda p : geopath.getPathLength(float(v[0]), float(v[1]), float(p[0][0]), float(p[0][1])))
          
    def random_route(self,data,original):
        output = [original]
        for i in data:
            for j in data[i]:
                if j not in output:
                    output.append(j)
        output.remove(original)
        random.shuffle(output)
        return data, [original]+output
    
    def get_rute_barang3(self, port, original_port, full_port, kapal):
        data_kode_barang = self.split_barang_dekat_jauh(port)
        self.split_data_for_TL(data_kode_barang["Jarak Jauh"], kapal,full_port)
        self.split_data_for_R(data_kode_barang["Jarak Dekat"], kapal,full_port)
        
    def split_data_for_R(self, data, kapal, full_port):
        mode = random.random()
        mode = 0.2
        if mode <= 0.3:
            for kpl in kapal:
                if kpl.kategori not in ["TL", "PL"]:
                    original_port = kpl.rute_name[0]
                    kpl.add_rute(self,self.random_route(data,original_port))
        else:
            pel_loc = {i['Nama Pelabuhan']:[i["Latitude"],i["Longitude"]] for i in full_port}
            pel_p_loc = {i['Nama Pelabuhan']:[i["Latitude"],i["Longitude"]] for i in full_port if i["Tipe"] == "P"}
            
            
            output = self.split_data_base_on_location(pel_loc, pel_p_loc, data)
            

#            pel_bobot = ({name: sum([j["Bobot"] for j in self.lis_pelabuhan[name].barang]) for name in self.lis_pelabuhan})
            pel_bobot_ = ([{j["Kode Barang"]: j["Bobot"] for j in self.lis_pelabuhan[name].barang} for name in self.lis_pelabuhan])
            pel_bobot = {}
            for i in pel_bobot_:
                for k in i :
                    pel_bobot[k] = i[k]
            
            sorted_pel = (sorted([{i : sum([pel_bobot[k] for k in output[i]]) } for i in output], key= lambda k:list(k.values())[0], reverse = True))
            
            ori = []
            for kpl in kapal:
                if kpl.kategori not in ["TL", "PL"]:
                    ori.append({"name":[kpl.nama], "poss":pel_loc[kpl.rute_name[0]]})
            
            list_kpl_terdekat = {}
            for i in pel_p_loc:
                a = (i, sorted(ori, key = lambda p : geopath.getPathLength(float(pel_p_loc[i][0]), float(pel_p_loc[i][1]), float(p["poss"][0]), float(p["poss"][1]))))
                list_kpl_terdekat[a[0]] = [i["name"][0] for i in a[1]]
            
            
            priority = ([ list_kpl_terdekat[list(j.keys())[0]][:int(len(list_kpl_terdekat[list(j.keys())[0]])*(list(j.values())[0]/sum([ list(i.values())[0] for i in sorted_pel])))+2] for n,j in enumerate(sorted_pel)])
            
            output2 = {}
            
            for i in range(len(sorted_pel)):
                for n, name in enumerate(priority[i]):
                    
                    if name not in output2.keys():
                        output2[name] = output[list(sorted_pel[i].keys())[0]]
                    else:
                        if n == 0 :
                            a = output[list(sorted_pel[i].keys())[0]]
                            for k in a:
                                output2[name].update({k :output[list(sorted_pel[i].keys())[0]][k]})
                        else:
                            a = random.sample(list(output[list(sorted_pel[i].keys())[0]]), 1+ int(random.random()*len(output[list(sorted_pel[i].keys())[0]])))
                            for k in a:
                                output2[name].update({k :output[list(sorted_pel[i].keys())[0]][k]})
            for i in  ori:
                if i["name"][0] not in list(output2.keys()):
                    output2[i["name"][0]] = output[list(sorted_pel[0].keys())[0]]
                    
            for kpl in kapal:
                if kpl.kategori not in ["TL", "PL"]:
                    kpl.add_rute(self,self.random_route(output2[kpl.nama],kpl.rute_name[0]))
            
            for tmp in output2:
                k = list(output2[tmp].keys())
                
    def split_data_for_TL(self, data, kapal,full_port):
        mode = random.random()
        mode = 0.8
        if mode >= 0.5:
            for kpl in kapal:
                if kpl.kategori in ["TL", "PL"]:
                    original_port = kpl.rute_name[0]
                    kpl.add_rute(self,self.random_route(data,original_port))
        else:
            pel_loc = {i['Nama Pelabuhan']:[i["Latitude"],i["Longitude"]] for i in full_port}
            ori = {}
            for kpl in kapal:
                if kpl.kategori in ["TL", "PL"]:
                    ori[kpl.nama] = pel_loc[kpl.rute_name[0]]
                    
            output = self.split_data_base_on_location(pel_loc, ori, data)
            output = self.merge_data(output)
            for kpl in kapal:
                if kpl.kategori in ["TL", "PL"]:
                    kpl.add_rute(self,self.random_route(output[kpl.nama],kpl.rute_name[0]))

            
    def merge_data(self, output):
        
        data_merge = {}
        for kat in output.keys():
            
            kode_list = list(output[kat].keys())
            random.shuffle(kode_list)
            
            data_merge[kat] = kode_list[:int(random.random()*len(kode_list))]
        
        keys = list(output.keys())
        for i in range(len(keys)):
            for kode in data_merge[keys[i]]:
                idx = keys[(i+1)%len(keys)]
                output[idx][kode] = output[keys[i]][kode]
        return output
        
            
                    
    def split_data_base_on_location(self, convertion, kategori, barang, max_data = None):
        output = {}
        value = list(kategori.values())
        key_name = list(kategori.keys())

        for p in key_name:
            output[p] = {}
        for key,val in barang.items():
            poss = None
            for k in val:
                idx = self.find_closest(value, convertion[k])

                if poss is None:
                    poss = [key_name[value.index(idx)], geopath.getPathLength(idx[0],idx[1],convertion[k][0],convertion[k][1])]
                if poss[1] > geopath.getPathLength(idx[0],idx[1],convertion[k][0],convertion[k][1]):
                    poss = [key_name[value.index(idx)], geopath.getPathLength(idx[0],idx[1],convertion[k][0],convertion[k][1])]
                
            if poss is not None:
                output[poss[0]][key] = val
                
        return output
                    
            
        
    def split_barang_dekat_jauh(self, port):
        data_kode_barang = {}
        data_kode_barang["Jarak Jauh"] = {}
        data_kode_barang["Jarak Dekat"] = {}
        
        for items in self.lis_pelabuhan.values():
            for brg in items.barang:
                asal = brg["Asal Pelabuhan"]
                transit = brg["Transit"]
                tujuan = brg["Tujuan Pelabuhan"]
                if (port[asal] == "U") :
                    data_kode_barang["Jarak Jauh"][brg["Kode Barang"]] = [asal,transit]
                    data_kode_barang["Jarak Dekat"][brg["Kode Barang"]] = [transit,tujuan]
                    
                elif(port[tujuan] == "U"):
                    data_kode_barang["Jarak Jauh"][brg["Kode Barang"]] = [transit,tujuan]
                    data_kode_barang["Jarak Dekat"][brg["Kode Barang"]] = [asal,transit]
                else:                    
                    if transit is not "None":
                        data_kode_barang["Jarak Dekat"][brg["Kode Barang"]] = [asal,transit,tujuan]
                    else:
                        data_kode_barang["Jarak Dekat"][brg["Kode Barang"]] = [asal,tujuan]   
        return data_kode_barang
                
    def get_rute_barang2(self, port, original_port, full_port):
        data_kode_barang = {}
        data_kode_barang["Jarak Jauh"] = {}
        data_kode_barang["Jarak Dekat"] = {}
        for items in self.lis_pelabuhan.values():
            for brg in items.barang:
                asal = brg["Asal Pelabuhan"]
                transit = brg["Transit"]
                tujuan = brg["Tujuan Pelabuhan"]
                
                if (port[asal] == "U") :
                    data_kode_barang["Jarak Jauh"][brg["Kode Barang"]] = [asal,transit]
                    data_kode_barang["Jarak Dekat"][brg["Kode Barang"]] = [transit,tujuan]
                    
                elif(port[tujuan] == "U"):
                    data_kode_barang["Jarak Jauh"][brg["Kode Barang"]] = [transit,tujuan]
                    data_kode_barang["Jarak Dekat"][brg["Kode Barang"]] = [asal,transit]
                else:                    
                    if transit is not "None":
                        data_kode_barang["Jarak Dekat"][brg["Kode Barang"]] = [asal,transit,tujuan]
                    else:
                        data_kode_barang["Jarak Dekat"][brg["Kode Barang"]] = [asal,tujuan]
        p_list = {}
        output = {}
        number_barang = {}
        for p in original_port:
            output[p] = {}
            number_barang[p] = 0
            ori = original_port[p][1]
            p_list[p] = ([[i["Latitude"],i["Longitude"]] for i in (filter(lambda pel : pel['Nama Pelabuhan'] == ori, full_port))])
        value = list(p_list.values())
        key_name   = list(p_list.keys())
        
        a =({i['Nama Pelabuhan']:[i["Latitude"],i["Longitude"]] for i in full_port})
        
        for key,val in data_kode_barang["Jarak Dekat"].items():
            poss = None
            for k in val:
                idx = self.find_closest(value, a[k])
                if poss is None:
                    poss = [key_name[value.index(idx)], geopath.getPathLength(idx[0][0],idx[0][1],a[k][0],a[k][1])]
                if poss[1] < geopath.getPathLength(idx[0][0],idx[0][1],a[k][0],a[k][1]):
                    poss = [key_name[value.index(idx)], geopath.getPathLength(idx[0][0],idx[0][1],a[k][0],a[k][1])]
            if poss is not None:
                output[poss[0]][key] = val
                number_barang[poss[0]] += 1
        
        for i in output:
            if output[i] == {}:
                a = max(number_barang, key = number_barang.get)
                output[i] = output[a]
        data_kode_barang["Jarak Dekat"] = output
        return data_kode_barang
    
    def get_barang_sampai(self):
        data = []
        for items in self.lis_pelabuhan.values():
            barang = items.barang_sampai
            for i in barang.values():
                data.append(i)
        return data
    
    def get_barang_transit(self):
        data = []
        for items in self.lis_pelabuhan.values():
            barang = items.barang_transit
            for i in barang.values():
                data.append(i)
        return data
    
    def loading_barang(self, kapal, pel_singgah, c):
        delete_list = [] 
                      
        for n, brg in enumerate(self.lis_pelabuhan[pel_singgah].barang):
            # if brg["Tujuan Pelabuhan"] in self.pel_cuaca_tinggi and kapal.kategori == "PR" and :
            #     pass
            # else: 
            new_barang = kapal.ambil_barang(brg)
            if new_barang == None:
                delete_list.append(n)
            else:
                if new_barang["Bobot"] != self.lis_pelabuhan[pel_singgah].barang[n]["Bobot"]:
                    self.lis_pelabuhan[pel_singgah].barang[n]["Bobot"] = new_barang["Bobot"]
                    
        if delete_list != []:
            a = [v for i,v in enumerate(self.lis_pelabuhan[pel_singgah].barang) if i not in delete_list]
            self.lis_pelabuhan[pel_singgah].barang = a
        
        #Transit
        delete_list = []                
        for n, kode_barang in enumerate(self.lis_pelabuhan[pel_singgah].barang_transit):
            if self.lis_pelabuhan[pel_singgah].barang_transit[kode_barang]["Tujuan Pelabuhan"] in self.pel_cuaca_tinggi and kapal.kategori == "PR":
                pass
            else: 
                new_barang = kapal.ambil_barang(self.lis_pelabuhan[pel_singgah].barang_transit[kode_barang],mode = "Transit")
                if new_barang == None:
                    delete_list.append(n)
                else:
                    if new_barang["Bobot"] != self.lis_pelabuhan[pel_singgah].barang_transit[kode_barang]["Bobot"]:
                        self.lis_pelabuhan[pel_singgah].barang_transit[kode_barang]["Bobot"] = new_barang["Bobot"]
    
        if delete_list != []:
            a = {kode_barang:self.lis_pelabuhan[pel_singgah].barang_transit[kode_barang] for i,kode_barang in enumerate(self.lis_pelabuhan[pel_singgah].barang_transit) if i not in delete_list}
            self.lis_pelabuhan[pel_singgah].barang_transit = a

    
    def checking_posisi(self, kapal):
        # self.pel_cuaca_tinggi = [i.nama for i in self.lis_pelabuhan.values() if i.is_high]
        self.pel_cuaca_tinggi = []
        for kpl in kapal:
            posisi = kpl.before_loc
            posisi = kpl.rute2["nama"].split(" - ")[0]
            hasil = {name:pel for name, pel in self.lis_pelabuhan.items() if (pel.nama == posisi and kpl.is_singgah) }
            if hasil != {}:
                pel_singgah = list(hasil.keys())[0]
                kpl.update_waktu_singgah(pel_singgah)
                kpl.update_kapasitas()

                a = self.unloading_barang(kpl, pel_singgah)
                kpl.update_kapasitas()
                self.loading_barang(kpl, pel_singgah,a)
                kpl.update_kapasitas()

                tujuan = []
                for i in kpl.barang:
                    if kpl.kategori == "PR":
                        if i["Transit"] == "None":
                            if i["Tujuan Pelabuhan"] not in self.pel_cuaca_tinggi:
                                tujuan += [i["Tujuan Pelabuhan"]] 
                        else:
                            if type(i["Transit"]) == list:
                                trans = i["Transit"][0]
                                if trans not in self.pel_cuaca_tinggi:
                                    tujuan += trans
                            else:
                                trans = i["Transit"]
                                if trans not in self.pel_cuaca_tinggi:
                                    tujuan += trans
                    else:
                        if i["Transit"] == "None":
                            tujuan += [i["Tujuan Pelabuhan"]] 
                        else:
                            if type(i["Transit"]) == list:
                                trans = i["Transit"][0]
                                tujuan += trans
                            else:
                                trans = i["Transit"]
                                tujuan += trans
                        
                for pel in kpl.rute_name:
                    list_barang = self.lis_pelabuhan[pel].barang
                    list_barang2 = self.lis_pelabuhan[pel].barang_transit.values()
                    
                    if kpl.kategori in ["PR"]:
                        tujuan += [i["Tujuan Pelabuhan"] for i in list_barang if (i["Tujuan Pelabuhan"] in kpl.rute_name and i["Asal Pelabuhan"] not in self.pel_cuaca_tinggi)]
                        tujuan += [i["Transit"] for i in list_barang if (i["Transit"] in kpl.rute_name and i["Tujuan Pelabuhan"] not in kpl.rute_name and i["Transit"] not in self.pel_cuaca_tinggi) ]
                        tujuan += [i["Tujuan Pelabuhan"] for i in list_barang2 if (i["Tujuan Pelabuhan"] in kpl.rute_name  and i["Tujuan Pelabuhan"] not in self.pel_cuaca_tinggi)]
                          
#                          tujuan += [i["Tujuan Pelabuhan"] for i in list_barang2 if (i["Tujuan Pelabuhan"] in kpl.rute_name and i["Tujuan Pelabuhan"]  not in self.pel_cuaca_tinggi)]
#                          tujuan += [i["Tujuan Pelabuhan"] for i in list_barang if (i["Tujuan Pelabuhan"] in kpl.rute_name and i["Tujuan Pelabuhan"]  not in self.pel_cuaca_tinggi)]
#                          tujuan += [i["Transit"] for i in list_barang if (i["Transit"] in kpl.rute_name and i["Tujuan Pelabuhan"] not in kpl.rute_name and i["Asal Pelabuhan"] not in self.pel_cuaca_tinggi and i["Transit"] in self.pel_cuaca_tinggi) ]

                    
                    elif kpl.kategori in ["TL", "PL"]:
                        tujuan += [i["Tujuan Pelabuhan"] for i in list_barang if i["Tujuan Pelabuhan"] in kpl.rute_name]
                        tujuan += [i["Transit"] for i in list_barang if (i["Transit"] in kpl.rute_name and i["Tujuan Pelabuhan"] not in kpl.rute_name)]
                        tujuan += [i["Tujuan Pelabuhan"] for i in list_barang2  if i["Tujuan Pelabuhan"] in kpl.rute_name ]

                # if list(set(kpl.rute_name).intersection(set(tujuan))) == [] and  (kpl.beban_angkut == 0):
                if list(set(kpl.rute_name).intersection(set(tujuan))) == [] and  (kpl.beban_angkut == 0):
                      kpl.set_barang_kosong(True)
                else:
                      kpl.set_barang_kosong(False)
        
    def unloading_barang(self,kapal, pel_singgah):
        delete_index = []
        a = []
        for n, brg in enumerate(kapal.barang):
            
            if brg["Tujuan Pelabuhan"] in kapal.emergency_transit.keys():
                if kapal.emergency_transit[ brg["Tujuan Pelabuhan"]] == pel_singgah:
                    delete_index.append(n)
                    if brg["Kode Barang"] in self.lis_pelabuhan[pel_singgah].barang_transit.keys():
                        self.lis_pelabuhan[pel_singgah].barang_transit[brg["Kode Barang"]]["Bobot"] += brg["Bobot"]                    
                    else:
                        self.lis_pelabuhan[pel_singgah].barang_transit[brg["Kode Barang"]] = brg
                    a.append(brg["Kode Barang"])

            if (brg["Tujuan Pelabuhan"].lower() ==  pel_singgah.lower()):
                delete_index.append(n)
                if brg["Kode Barang"] in self.lis_pelabuhan[pel_singgah].barang_sampai.keys():
                    self.lis_pelabuhan[pel_singgah].barang_sampai[brg["Kode Barang"]]["Bobot"] += brg["Bobot"]                    
                else:
                    self.lis_pelabuhan[pel_singgah].barang_sampai[brg["Kode Barang"]] = brg
                a.append(brg["Kode Barang"])
            
            elif brg["Transit"] != "None":
                # print("=======")
                # print(brg["Transit"], pel_singgah)
                condition  = False
                if type(brg["Transit"]) != list:
                    condition = (brg["Transit"].lower() ==  pel_singgah.lower() and (brg["Tujuan Pelabuhan"] not in  kapal.rute_name))
                    if  pel_singgah ==  brg["Transit"]:
                        brg["Transit"] = "None"
                else:
                    condition = ((brg["Transit"][0].lower() ==  pel_singgah.lower()) and (brg["Tujuan Pelabuhan"] not in  kapal.rute_name))
                    if pel_singgah == brg["Transit"][0]:
                        if len(brg["Transit"]) > 1:
                            brg["Transit"] = [brg["Transit"][1]]
                        else:
                            brg["Transit"] = "None"

                # print(brg["Transit"], pel_singgah, condition)
                if  condition:
                    delete_index.append(n)
                    if brg["Kode Barang"] in self.lis_pelabuhan[pel_singgah].barang_transit.keys():
                        self.lis_pelabuhan[pel_singgah].barang_transit[brg["Kode Barang"]]["Bobot"] += brg["Bobot"]
                    else:
                        self.lis_pelabuhan[pel_singgah].barang_transit[brg["Kode Barang"]] = brg
                    a.append(brg["Kode Barang"])
                
        kapal.barang = [v for i,v in enumerate(kapal.barang) if i not in delete_index]
        return a
  
      
    def breed2(self, parent1, parent2):
        kode_barang_1 = []
        for kpl1 in parent1:
            kode_barang_1.append(kpl1.full_rute_barang)
            
        output = []
        for i in range(len(parent1)):
#            if kode_barang_1[i].keys() == kode_barang_2[i].keys():
            if True:
                
                rute1 = parent1[i].get_rute()[0]
                rute2 = parent2[i].get_rute()[0]
                
                origin_port = rute1[0]
                
                child = []
                childP1 = []
                childP2 = []
            
                geneA = int(random.random() * len(rute1))
                geneB = int(random.random() * len(rute1))
                
                startGene = min(geneA, geneB)
                endGene = max(geneA, geneB)
                
                for j in range(startGene, endGene):
                    childP1.append(rute1[j])
                childP2 = [item for item in rute2 if item not in childP1]
                child = childP1 + childP2
                
                child.remove(origin_port)
                child.insert(0, origin_port)
                
                output.append((kode_barang_1[i],child))
        return output
                
        

    def breed(self, parent1, parent2):
        kode_barang_1 = []
        kategori = {}
        for kpl1 in parent1:
            kode_barang_1.append(kpl1.full_rute_barang)
            if kpl1.kategori not in kategori.keys():
                kategori[kpl1.kategori] = 0
            kategori[kpl1.kategori] +=1
            
        kode_barang_2 = []
        for kpl2 in parent2:
            kode_barang_2.append(kpl2.full_rute_barang)
        
        not_selected = None
        output = []
        for i in range(len(parent1)):
#            if kode_barang_1[i].keys() == kode_barang_2[i].keys():
            if True:
                
                rute1 = parent1[i].get_rute()[0]
                rute2 = parent2[i].get_rute()[0]
                
                origin_port = rute1[0]
                
                child = []
                childP1 = []
                childP2 = []
            
                geneA = int(random.random() * len(rute1))
                geneB = int(random.random() * len(rute1))
                
                startGene = min(geneA, geneB)
                endGene = max(geneA, geneB)
                
                for j in range(startGene, endGene):
                    childP1.append(rute1[j])
                childP2 = [item for item in rute2 if item not in childP1]
                child = childP1 + childP2
                
                child.remove(origin_port)
                child.insert(0, origin_port)
                
                output.append((kode_barang_1[i],child))
            
            else:
                mode = random.random()
                mode = 0.8
                if (mode > 0.5) or (kategori[parent1[i].kategori] >1):#Merge
                    rute1 = parent1[i].get_rute()
                    rute2 = parent2[i].get_rute()
                    index = int(random.random() * (len(rute1)-1))+1
                    [rute1.insert(n+index, i) for n,i in enumerate(rute2)]
                    kode_barang_1[i].update(kode_barang_2[i])
                    
                    output.append((kode_barang_1[i],rute1))
                    
                else:
                    if len(parent1[i].get_rute()[0]) > len(parent2[i].get_rute()[0]):
                        rute1 = parent1[i].get_rute()[0]
                        rute2 = parent2[i].get_rute()[0]
                    elif len(parent1[i].get_rute()[0]) < len(parent2[i].get_rute()[0]):
                        rute1 = parent2[i].get_rute()[0]
                        rute2 = parent1[i].get_rute()[0]
                    else:
                        rute1 = parent1[i].get_rute()[0]
                        rute2 = parent2[i].get_rute()[0]
                        
                    differ = list(set(rute1).difference(set(rute2)))
                    
                    kode_barang_1[i].update(kode_barang_2[i])
                    if not_selected is not None:
                        kode_barang_1[i].update(not_selected)
                    
                    selected = {}
                    not_selected = {}
                    for key in  kode_barang_1[i]:
                        for rut_name in differ:
                            if rut_name in kode_barang_1[i][key] :
                                not_selected[key] = kode_barang_1[i][key]
                            else:
                                selected[key] = kode_barang_1[i][key]
                    
                    rute1 = list(set(rute1).difference(set(differ)))
                    
                    child = []
                    childP1 = []
                    childP2 = []
                
                    geneA = int(random.random() * len(rute1))
                    geneB = int(random.random() * len(rute1))
                    
                    startGene = min(geneA, geneB)
                    endGene = max(geneA, geneB)
                    
                    for i in range(startGene, endGene):
                        childP1.append(rute1[i])
                    childP2 = [item for item in rute2 if item not in childP1]
                    child = childP1 + childP2
                    
                    output.append((kode_barang_1[i],rute1))
                    
        return output
    
                
class Kapal():
    def __init__(self,pelabuhan, nama, kategori, kapasitas, rute, speed, data, time_step = 0.1):
        
        self.rute_name = rute
        self.time_step = time_step #jam
#        self.time_step = 10
        self.data = data
        self.speed = speed
        self.bm_time = data["bm_time"]
        self.waktu_singgah_max =  data["bm_time"]
        self.waktu_singgah_max = 12
        
        
        if kategori.lower() == "tl": 
            self.option = "{color : '#ff0000', radius : 3,fillOpacity:0.7}"

            
        elif kategori.lower() == "pl":
            self.option = "{color : '#00ad06', radius : 3,fillOpacity:0.7}"
            
        else:
            self.option = "{color : '#000000', radius : 3,fillOpacity:0.7}"

            
        self.singgah = 0
        self.is_singgah = False
        
        self.rute = pelabuhan.get_full_path(self.speed*1000*self.time_step,rute)
        
        self.nama = nama
        self.kategori = kategori
        self.kapasitas = kapasitas
        
        self.lama_perjalanan = 0
        self.marker = None
        self.beban_angkut = 0
        self.cost = 0
        self.barang_kosong = False
        
        self.skip_step = 0

        self.emergency_transit = {}
        
        path = 0
        for i in self.rute:
            for n, j in enumerate(i["rute"][:-1]):
                loc1 = i["rute"][n]
                loc2 = i["rute"][n+1]
                l = geopath.getPathLength(loc1[0],loc1[1],loc2[0],loc2[1])/1000
                path += l
        self.total_path = path

        self.current_position = 0
        self.started = True
        self.count = 0
        self.count_rute = 0
        self.before_loc = self.rute[self.count_rute]["rute"][self.count]
        
        self.rute2 = None
        self.berlabuh = False
        
        self.barang = []
        
    def reset(self, pelabuhan):
        self.singgah = 0
        self.is_singgah = False
        self.lama_perjalanan = 0
        self.beban_angkut = 0
        self.cost = 0
        self.barang_kosong = False
        self.skip_step = 0
        
        path = 0
        for i in self.rute:
            for n, j in enumerate(i["rute"][:-1]):
                loc1 = i["rute"][n]
                loc2 = i["rute"][n+1]
                l = geopath.getPathLength(loc1[0],loc1[1],loc2[0],loc2[1])/1000
                path += l
        self.total_path = path


        self.current_position = 0
        self.started = True
        self.count = 0
        self.count_rute = 0
#        self.before_loc = self.rute[self.count_rute]["rute"][self.count]
        
        self.rute2 = None
        self.berlabuh = False
        
        self.barang = []
        if self.marker is not None:
              self.marker.setLatLng(self.before_loc )
        
    def add_rute(self,pelabuhan, rute):
        self.rute_name = [i for i in rute[1] if i != "None"]
        self.current_port = self.rute_name[0]
        self.rute = pelabuhan.get_full_path(self.speed*1000*self.time_step,rute[1])
        self.full_rute_barang = rute[0]
        
        if len(self.rute_name) > 1:
            self.rute2 = pelabuhan.get_full_path(self.speed*1000*self.time_step,[self.rute_name[0],self.rute_name[1]])[0]
        
        
        
    def get_rute(self):
        return self.rute_name, self.full_rute_barang
        
    def draw(self, map_obj):
        self.marker = L.circleMarker(self.rute[0]["rute"][0],options= self.option)
        self.marker.bindTooltip(self.nama.capitalize())
        map_obj.addLayer(self.marker)
        
    def update_kapasitas(self):
        self.beban_angkut = sum([i['Bobot'] for i in self.barang])
        
    def update_waktu_singgah(self, name):
        if name not in self.bm_time.keys():
            x= [i for i in self.bm_time.values()]
            nilai = max(set(x), key= x.count)
            self.waktu_singgah_max = nilai
        else:
            self.waktu_singgah_max = self.data["bm_time"][name] + self.data["port_storage_time"][name]
#        self.waktu_singgah_max = 5
        
    def update(self, pelabuhan):
        if self.started:
            self.check_available_port(pelabuhan)
            self.started = False
            
        if (not self.is_singgah):
#            if len(self.rute[self.count_rute]["rute"]) >  self.count:
            if len(self.rute2["rute"]) >  self.count:
                self.berlabuh = False
                self.beban_angkut = sum([i['Bobot'] for i in self.barang])
                
                if self.rute2 is None:
                    loc1 = self.rute[self.count_rute]["rute"][self.count]
                    loc2 = self.before_loc
                else:
                    loc1 = self.rute2["rute"][self.count]
                    loc2 = self.before_loc
                    
                self.before_loc = loc1
                l = geopath.getPathLength(loc1[0],loc1[1],loc2[0],loc2[1])/1000
                self.cost += self.cost_function_perjalanan(l)
                
                self.current_position += l
                if self.marker is not None:
                    self.marker.setLatLng(loc1)
                self.curren_destination = self.rute[self.count_rute]["nama"]
                self.count = (self.count+1)
                
                self.lama_perjalanan += (self.time_step*60)
            else :
        
                self.count_rute = (self.count_rute+1) % len(self.rute)
                self.lama_perjalanan += (self.time_step*60)
                
                self.berlabuh = True
                self.is_singgah = True
                self.check_available_port(pelabuhan)
                
        elif self.is_singgah:
            
            if self.singgah <= self.waktu_singgah_max*60 or (self.barang_kosong) :
                # if self.barang_kosong and self.beban_angkut == 0:
                if self.barang_kosong :
                    pass
                else:
                    self.cost += self.cost_function_singgah((self.time_step*60))
                    self.lama_perjalanan += (self.time_step*60)
                    self.singgah += (self.time_step*60)
            else:
                self.lama_perjalanan += (self.time_step*60)
                self.singgah = 0
                self.is_singgah = False
                self.count = 0

#        if not(self.barang_kosong) and self.beban_angkut == 0 and self.is_singgah:
#              self.is_singgah = False
                
    def get_data(self):
        return {
                "Nama" : self.nama, 
                "Kategori" : self.kategori, 
                "Kapasitas" : str(self.beban_angkut)+"/"+str(self.kapasitas), 
                "Lama Perjalanan" : str(timedelta(minutes=self.lama_perjalanan))[:-3], 
#                "Lokasi Sekarang": str(int(100*self.current_position/self.total_path))+"%",
                "Lokasi" : self.rute2["nama"], 
                "Total" : str(int(self.cost))
                }
        
    def cost_function_perjalanan(self,jarak):
        name = self.rute2["nama"].split(" - ")[0]
        total_cost_travel_time = self.data["inventory_cost"][name] *self.data["bm_time"][name] *(self.data["avg_docking_time"][name]*(jarak/self.speed))
        
        return total_cost_travel_time
    
    def cost_function_singgah(self,waktu):
        name = self.rute2["nama"].split(" - ")[0]
        total_cost_bongkar = 0
        total_cost_storage = 0
        if self.singgah < self.data["bm_time"][name]:
              total_cost_bongkar = self.beban_angkut * waktu * self.data["C_bm"][name]
        else:
              total_cost_storage = self.beban_angkut * waktu * self.data["C_storage"][name]
        cost_bongkar_time = self.data["inventory_cost"][name] * (self.beban_angkut /self.data["C_bm"][name])
        
        return total_cost_bongkar + total_cost_storage + cost_bongkar_time
        
    def ambil_barang(self,brg, mode = "No Transit"):
        barang = brg.copy()
        barang2 = brg.copy()
        if mode == "No Transit":
            condition = False
            if type(barang["Transit"]) != list:
                condition = (barang["Transit"] in self.rute_name and barang["Tujuan Pelabuhan"] not in self.rute_name) or (barang["Tujuan Pelabuhan"] in self.rute_name)
            else:
                condition =  (barang["Transit"][0] in self.rute_name and barang["Tujuan Pelabuhan"] not in self.rute_name) or (barang["Tujuan Pelabuhan"] in self.rute_name)
                
            # if (barang["Tujuan Pelabuhan"] in self.rute_name) or (condition) or (barang["Transit"] in self.rute_name and self.kategori in  ["TL","PL"]) :
            if condition:
                if (self.kapasitas - self.beban_angkut) != 0 :
                    ambil = barang['Bobot'] - (self.kapasitas - self.beban_angkut) 
                    
                    if ambil > 0 :
                        barang2['Bobot'] = (self.kapasitas - self.beban_angkut)
                        self.barang.append(barang2)
                        barang['Bobot'] = barang['Bobot'] - (self.kapasitas - self.beban_angkut) 
                    else:
                        self.barang.append(barang)
                        barang = None
        else:
            condition = False
            if barang["Tujuan Pelabuhan"] in self.rute_name:
                if (self.kapasitas - self.beban_angkut) != 0 :
                    ambil = barang['Bobot'] - (self.kapasitas - self.beban_angkut)
                    if ambil > 0 :
                        barang2['Bobot'] = (self.kapasitas - self.beban_angkut)
                        self.barang.append(barang2)
                        barang['Bobot'] = barang['Bobot'] - (self.kapasitas - self.beban_angkut) 
                    else:
                        self.barang.append(barang)
                        barang = None
            else:
                if type(barang["Transit"]) != list:
                    condition = (barang["Transit"] in self.rute_name and barang["Tujuan Pelabuhan"] not in self.rute_name and barang["Asal Pelabuhan"] not in self.rute_name) 
                else:
                    condition =  (barang["Transit"][0] in self.rute_name and barang["Tujuan Pelabuhan"] not in self.rute_name and barang["Asal Pelabuhan"] not in self.rute_name) 

                if (condition):
                    if (self.kapasitas - self.beban_angkut) != 0 :
                        ambil = barang['Bobot'] - (self.kapasitas - self.beban_angkut)
                        if ambil > 0 :
                            barang2['Bobot'] = (self.kapasitas - self.beban_angkut)
                            self.barang.append(barang2)
                            barang['Bobot'] = barang['Bobot'] - (self.kapasitas - self.beban_angkut) 
                            
                        else:
                            self.barang.append(barang)
                            barang = None
#        self.update_kapasitas()
        self.beban_angkut = sum([i['Bobot'] for i in self.barang])
        if mode != "No Transit":
            self.barang
        return barang
    
    def check_available_port(self, pelabuhan):

        self.emergency_transit = {k:v for k,v in self.emergency_transit.items() if k in pelabuhan.pel_cuaca_tinggi}    
    
        idx = self.rute_name.index(self.current_port)
        next_port = self.rute_name[(idx+1) % len(self.rute_name)]

        
        self.skip_step = 0
        inc = 0
        next_trip = [self.current_port, next_port]
        
        for i in range(len(self.rute_name)):
            index = (i + idx + 1) % len(self.rute_name)
            n_port = self.rute_name[index]
            inc += 1

            if n_port != "None":
                if self.beban_angkut == self.kapasitas:
                    for brg in self.barang:
                    #    if brg["Tujuan Pelabuhan"] == n_port or  (brg["Transit"] == n_port and self.kategori in ["PL"] ):
                        if brg["Tujuan Pelabuhan"] == n_port or  (brg["Transit"] == n_port and brg["Asal Pelabuhan"] in self.rute_name and brg["Tujuan Pelabuhan"] not in self.rute_name):
                            if brg["Bobot"] > 0:
                                next_trip[1] = (n_port)
                                self.skip_step = inc
                                break
                else :
                    for brg in  pelabuhan.lis_pelabuhan[n_port].barang:
                        if type(brg["Transit"]) == list:
                            trans = brg["Transit"][0]
                        else:
                            trans = brg["Transit"]
                            
                        if (brg["Asal Pelabuhan"] == n_port and  (trans in self.rute_name) and brg["Tujuan Pelabuhan"] not in self.rute_name) or (brg["Tujuan Pelabuhan"] in self.rute_name):
                            if brg["Bobot"] > 0:
                                next_trip[1] = (n_port)
                                self.skip_step = inc
                                break
                        
                    for brg in  pelabuhan.lis_pelabuhan[n_port].barang_transit.values():
                        if (brg["Tujuan Pelabuhan"] in self.rute_name):
                            if brg["Bobot"] > 0:
                                next_trip[1] = (n_port)
                                self.skip_step = inc
                                break
                        if type(brg["Transit"]) == list:
                            trans = brg["Transit"][0]
                        else:
                            trans = brg["Transit"]

                        if trans == n_port :
                            if brg["Bobot"] > 0:
                                next_trip[1] = (n_port)
                                self.skip_step = inc
                                break
                        
                    for brg in self.barang:
                        if brg["Tujuan Pelabuhan"] == n_port:
                            if brg["Bobot"] > 0:
                                next_trip[1] = (n_port)
                                self.skip_step = inc
                                break 
                        if brg["Transit"] != "None":
                            if type(brg["Transit"]) == list:
                                trans = brg["Transit"][0]
                            else:
                                trans = brg["Transit"]
                            
                            if trans == n_port:
                                if brg["Bobot"] > 0:
                                    next_trip[1] = (n_port)
                                    self.skip_step = inc
                                    break 
                        
                if (next_trip[1] !=   self.rute_name[(idx+1) % len(self.rute_name)]):
                    break

        # if self.kategori == "PR":
        #     min_d = None
        #     next_emergency = None
        #     if next_trip[1] in pelabuhan.pel_cuaca_tinggi:
        #         idx = self.rute_name.index(next_trip[1])
        #         if self.beban_angkut == self.kapasitas:
        #             for i in range(len(self.rute_name)):
        #                 emergenc_port = self.rute_name[(idx+1+i) % len(self.rute_name)]
        #                 if pelabuhan.lis_pelabuhan[emergenc_port].kategori == "P":
        #                     rute = pelabuhan.rute[(next_trip[1],emergenc_port)]
        #                     d = sum([ geopath.getPathLength(rute[i][0],rute[i][1],rute[i+1][0],rute[i+1][1]) for i in range(len(rute)-1)])
        #                     if min_d == None:
        #                         min_d = d
        #                         next_emergency = emergenc_port
        #                     elif min_d > d:
        #                         next_emergency = emergenc_port
        #                         min_d = d

        #             self.emergency_transit[ next_trip[1]] = next_emergency
        #             next_trip[1] = next_emergency
        #         else:
        #             next_trip[1] = self.rute_name[(idx+1) % len(self.rute_name)]

        self.rute2 = pelabuhan.get_full_path(self.speed*1000*self.time_step,next_trip)[0]
        self.current_port = next_trip[1]
        
    def set_barang_kosong(self, barang_kosong):
        self.barang_kosong = barang_kosong
          
        
        
    
        
        
        
