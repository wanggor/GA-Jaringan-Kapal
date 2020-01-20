from utils import preprocessing, geopath
from models import logistic_models as ls
import matplotlib.pyplot as plt
import random
import operator
import pandas as pd
import numpy as np
import datetime
import progressbar
import pickle
import os

class GA_Trainer():
    def __init__(self, path_data, path_ship, popSize, eliteSize, mutationRate, timestep = 0.1, draw = False):
        self.popSize = popSize
        self.eliteSize = eliteSize
        self.mutationRate = mutationRate
        
        self.draw = draw
        self.timestep = timestep
        self.path = [path_data,path_ship]
        self.data = preprocessing.parsing_data_2(self.path)
        # for i in range(len(self.data["Wave"])):
        #     print(self.data["Wave"][i]["Tanggal Awal"], self.data["Wave"][i]["Tanggal Akhir"], self.data["Wave"][i]["Dawera/Dawelor"])
        self.original_port = { i["nama"]: [i["kategori"],i["rute"][0]]for i in self.data["Kapal"]}
        self.createPelabuhan()
        self.p = 0
        self.max_itter = None

        self.y_plot = []

        self.bar_char_data = []

        self.data_output = "Generation\tRoute\tItteration\tCost\n"
        self.itteration = 0

    def createPelabuhan(self):
        self.pelabuhan = ls.JaringanPelabuhan()
        self.pelabuhan.add_multiPelabuhan(self.data["Daftar Pelabuhan"])
        self.pelabuhan.add_extraRoute(self.data["Rute"])
        # self.pelabuhan.add_rute_from_lis(self.data["Rute"])

        self.pelabuhan.add_barang(self.data["Barang"])
        self.pelabuhan.add_transit_cluster(self.data)
        self.Total_Nilai_Harga, self.data["Barang"] = self.pelabuhan.add_Harga(self.data["Harga Barang"], self.data["Daftar Pelabuhan"], self.data["Barang"])

    def initialPopulation(self, popSize):
        self.pupulation_kapal = []
        for i in range(0, popSize):
            self.pupulation_kapal.append(self.createObjectKapal())

        print("\n\n")
        print("Train Initialization ........")
        self.rankRoutes()
        print("\nInitialization Complete")

    def choose_route(self,data_barang, data,  original_port):
        route = [{}, []]
        for i in data.keys():
            if original_port in data[i]:
                route[1] = data[i].copy()
                random.shuffle(route[1])
                old_index = route[1].index(original_port)
                route[1].insert(0,route[1].pop(old_index))
                break
        
        for code, val in data_barang.items():
            if val[0] in route[1]:
                route[0][code] = val

        if route is not None:
            return route
        else:
            return None 
            
    def createObjectKapal(self):
        obj = [ls.Kapal(self.pelabuhan, kpl["nama"], kpl["kategori"], kpl["kapasitas"],kpl["max_voyage"], kpl["rute"], kpl["speed"],kpl,self.timestep) for kpl in self.data["Kapal"]]
        # self.data_kode_barang = self.pelabuhan.get_rute_barang3(self.data["port"],self.original_port, self.data["Daftar Pelabuhan"],obj)
        data_kode_barang = self.pelabuhan.get_rute_barang(self.data["port"],self.original_port, self.data["Daftar Pelabuhan"])
        for kpl in obj:

            original_port = kpl.rute_name[0]
            if kpl.kategori == "TL":
                # kpl.add_rute(self.pelabuhan,self.random_route(data_kode_barang["Jarak Jauh"],original_port, self.data["port"]))

                route = self.data["Spesial TL PELNI"]["Daftar Rute Tol Laut"].copy()
                random.shuffle(route)
                old_index = route.index(original_port)
                route.insert(0,route.pop(old_index))
                route = [data_kode_barang["Jarak Jauh"], route]
                kpl.add_rute(self.pelabuhan,route)
            elif kpl.kategori == "PL":

                # kpl.add_rute(self.pelabuhan,self.random_route(data_kode_barang["Jarak Jauh"],original_port, self.data["port"]))

    
                route = [original_port]
                data = self.data["Spesial TL PELNI"]["Daftar Rute Pelni"].copy()
                data.remove(original_port)

                while len(data) >0:
                    
                    d = None
                    min_index = 0
                    min_name = None
                    for n, i in enumerate(data):
                        asal = route[-1]
                        # print(self.pelabuhan.rute.keys())
                        if ( i, asal) not in self.pelabuhan.rute:
                            rute = self.pelabuhan.rute[( asal, i)]
                        else:
                            rute = self.pelabuhan.rute[( i, asal)]
                        l = sum([ geopath.getPathLength(rute[i][0],rute[i][1],rute[i+1][0],rute[i+1][1]) for i in range(len(rute)-1)])
                        if d ==  None:
                            d = l
                            min_name = i
                        if l < d:
                            d = l
                            min_index = n
                            min_name = i
                    data.remove(min_name)
                    route.append(min_name)
                route = [data_kode_barang["Jarak Jauh"], route]
                kpl.add_rute(self.pelabuhan,route)
                # print(kpl.rute_name)
            else:
                route = self.choose_route(data_kode_barang["Jarak Dekat"], self.data["Spesial PR"], original_port)
                kpl.add_rute(self.pelabuhan,route)
                # kpl.add_rute(self.pelabuhan,self.random_route(data_kode_barang["Jarak Dekat"],original_port))
        return obj

    def random_route(self,data,original, port_list):
        output = [original]
        for i in data:
            for j in data[i]:
                if j not in output:
                    output.append(j)

        for i in port_list:
            if port_list[i] in ["U", "P"]:
                if i not in output:
                    output.append(i)
        output.remove(original)
        random.shuffle(output)
        return data, [original]+output

    def check_wave(self, max_heigth):
        awal  = self.data["Wave"][self.wave_count]["Tanggal Awal"]
        akhir = self.data["Wave"][self.wave_count]["Tanggal Akhir"]

        if (self.date == akhir):
            if self.wave_count < len(self.data["Wave"])-1:
                self.wave_count = (self.wave_count+1)
        
        data = []
        if self.wave_count < len(self.data["Wave"]):
            data = [key for (key, item) in self.data["Wave"][self.wave_count].items() if (key not in ["Tanggal Awal", "Tanggal Akhir"] and item > max_heigth)]
        
        if data != self.data_wave:
            self.data_wave = data
            name_cuaca1 =  set(list(self.layer_cuaca.keys())).difference(set(self.data_wave))
            name_cuaca2 =  set(list(self.data_wave)).difference(set(list(self.layer_cuaca.keys())))
            [self.perubahan_cuaca(name_pel) for name_pel in name_cuaca1]
            [self.perubahan_cuaca(name_pel) for name_pel in name_cuaca2]

    def perubahan_cuaca(self, name_pel):
        obj = self.pelabuhan.lis_pelabuhan[name_pel.strip()]
        obj.is_high = not obj.is_high
        if obj.is_high:
            self.layer_cuaca[name_pel] = ""
        else:
            if name_pel in self.layer_cuaca.keys():
                del self.layer_cuaca[name_pel]

    def getFitness(self, index, mode = "no Test"):
        self.createPelabuhan()
        n = 0
        sisa = 1
        self.wave_count = 0
        # [i.reset(self.pelabuhan) for i in self.pupulation_kapal[index]]
        self.date = self.data["Wave"][0]["Tanggal Awal"]
        self.data_wave = []
        self.layer_cuaca = {}
        total = sum([float(i["Bobot"]) for i in self.data["Barang"]])
        widgets = [progressbar.FormatLabel(''),progressbar.Bar("="),"",progressbar.Percentage(), progressbar.FormatLabel(''),progressbar.FormatLabel('')]
        bar = progressbar.ProgressBar(total, widgets)
        bar.start()
        while True:
            n += 1
            self.check_wave(3)
            self.date = self.date + datetime.timedelta(seconds=0.1*60*60)
            [i.update(self.pelabuhan) for i in self.pupulation_kapal[index]]
            self.pelabuhan.checking_posisi(self.pupulation_kapal[index])
            
            total = sum([float(i["Bobot"]) for i in self.data["Barang"]])
            cost = sum([ float(i.get_data()["Total"]) for i in self.pupulation_kapal[index]])
            sisa = sum([ float(i["Total"]) for i in self.pelabuhan.get_barang()])
            revenue = sum([ float(i["Bobot"]) for i in self.pelabuhan.get_barang_sampai()])
            beban_kapal = sum([ float(i.beban_angkut) for i in self.pupulation_kapal[index]])
            transit = sum([ float(i["Total"]) for i in self.pelabuhan.get_barang_transit()])
            
            widgets[0] = progressbar.FormatLabel(f"{(index+1)}/{len(self.pupulation_kapal)} ")
            widgets[-2] = progressbar.FormatLabel(f" | Itter : {n} ")
            widgets[-1] = progressbar.FormatLabel(f" | Cost : {cost} ")
            bar.update(revenue)
            
            if self.draw:
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
            if self.max_itter is not None:
                if  n > self.max_itter*3 : 
                    break
            if (beban_kapal <= 0) and (sisa <= 0) and (transit <= 0):
                break
        if self.max_itter is not None:
            self.max_itter = max(n, self.max_itter)
        else:
            self.max_itter = n
        bar.finish()
        if mode == "no Test":
            self.data_output += f"{self.itteration}\t{index+1}\t{n}\t{cost}\n"
        elif mode == "test":
            pass
        return (cost)
    
    def rankRoutes(self):
        self.fitnessResults = {}
        for i in range(0,len(self.pupulation_kapal)):
            self.fitnessResults[i] = self.getFitness(i)
        self.fitnessResults = sorted(self.fitnessResults.items(), key = operator.itemgetter(1), reverse = False)

        
    def selection(self, eliteSize):
        self.selectionResults = []
        df = pd.DataFrame(np.array(self.fitnessResults), columns=["Index","Fitness"])
        df['cum_sum'] = df.Fitness.cumsum()
        df['cum_perc'] = 100*df.cum_sum/df.Fitness.sum()
        
        for i in range(0, eliteSize):
            self.selectionResults.append(self.fitnessResults[i][0])
        for i in range(0, len(self.fitnessResults) - eliteSize):
            pick = 100*random.random()
            for i in range(0, len(self.fitnessResults)):
                if pick <= df.iat[i,3]:
                    self.selectionResults.append(self.fitnessResults[i][0])
                    break

    def matingPool(self):
        self.matingpool = []
        for i in range(0, len(self.selectionResults)):
            index = self.selectionResults[i]
            self.matingpool.append(self.pupulation_kapal[index])
            
    def breedPopulation(self,eliteSize):
        children = []
        length = len(self.matingpool) - eliteSize
        
        for i in range(0,eliteSize):
            obj = []
            obj = [ls.Kapal(self.pelabuhan, kpl["nama"], kpl["kategori"], kpl["kapasitas"],kpl["max_voyage"], kpl["rute"], kpl["speed"],kpl,self.timestep) for kpl in self.data["Kapal"]]
            for n,m in enumerate(self.matingpool[i]):
                rute_name = m.rute_name
                barg = m.full_rute_barang
                obj[n].add_rute(self.pelabuhan, (barg, rute_name))
                # obj.append(m)
            children.append(obj)
            
        self.pool = random.sample(self.matingpool, len(self.matingpool))
        for i in range(0, length):
            child = self.pelabuhan.breed2(self.pool[i], self.pool[len(self.matingpool)-i-1])
            obj = [ls.Kapal(self.pelabuhan, kpl["nama"], kpl["kategori"], kpl["kapasitas"],kpl["max_voyage"], kpl["rute"], kpl["speed"],kpl,self.timestep) for kpl in self.data["Kapal"]]
            for i in range(len(child)):
                obj[i].add_rute(self.pelabuhan, child[i])
            children.append(obj)
        self.pupulation_kapal = children

    def mutate(self,  individual, mutationRate):
        for i in individual:
            if i.kategori != "PL":
                for swapped in range(len(i.get_rute()[0])-1):
                    if(random.random() < mutationRate):
                        swapped += 1
                        swapWith = int(random.random() * (len(i.get_rute()[0])-1))+1
                        
                        city1 = i.get_rute()[0][swapped]
                        city2 = i.get_rute()[0][swapWith]
                        
                        i.get_rute()[0][swapped] = city2
                        i.get_rute()[0][swapWith] = city1
#            i.add_rute(self.pelabuhan, [i.get_rute()[1],i.get_rute()[0]])
            
    def mutatePopulation(self, mutationRate):
        for ind in range(0, len(self.pupulation_kapal)):
            if ind != 0:
                self.mutate(self.pupulation_kapal[ind], mutationRate)

    def nextGeneration(self):
        self.itteration += 1
        print(f"\nGeneration : {self.itteration}")
        self.selection(self.eliteSize)
        self.matingPool()
        self.breedPopulation(self.eliteSize)
        self.mutatePopulation(self.mutationRate)
        self.rankRoutes()
        print(f"Best Route : {self.fitnessResults[0][0]+1} | Cost : {self.fitnessResults[0][1]}")
        self.y_plot.append(self.fitnessResults[0][1])
        self.data_output += f"{self.itteration}\t{self.fitnessResults[0][0]+1}\t\t{self.fitnessResults[0][1]}\n"
        
        return self.fitnessResults[0][1]

    def extract_best_route(self):
        index = self.fitnessResults[0][0]
        obj = [ls.Kapal(self.pelabuhan, kpl["nama"], kpl["kategori"], kpl["kapasitas"],kpl["max_voyage"], kpl["rute"], kpl["speed"],kpl,self.timestep) for kpl in self.data["Kapal"]]
        for n,m in enumerate(self.pupulation_kapal[index]):
            rute_name = m.rute_name
            barg = m.full_rute_barang
            obj[n].add_rute(self.pelabuhan, (barg, rute_name))
        # self.pupulation_kapal[index] = obj
        return obj

    def save(self):
        print("\nSaving Training Data ....")
        file_dir = "output"
        file_name = "model_"+ datetime.datetime.now().strftime('%d-%m-%y_%H-%M')
        file_dir = os.path.join(file_dir, file_name)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        obj = self.extract_best_route()
        file_pickle = os.path.join(file_dir, file_name+"_ship.pickle")
        pickle_out = open(file_pickle,"wb")
        pickle.dump(obj, pickle_out)
        pickle_out.close()

        file_pickle = os.path.join(file_dir, file_name+"_data.pickle")
        pickle_out = open(file_pickle,"wb")
        pickle.dump(self.data, pickle_out)
        pickle_out.close()

        file_pickle = os.path.join(file_dir, "log cost.csv")
        f = open(file_pickle,"w") 
        f.write(self.data_output)
        f.close()

        file_pickle = os.path.join(file_dir, "list nama rute.txt")
        with open(file_pickle, "w") as f:
            text = ""
            for n,i in enumerate(self.pupulation_kapal[self.fitnessResults[0][0]]):
                text += f"{n+1}. {i.nama.upper()} : "
                for j in i.rute_name:
                    text += f"{j}, "
                text += "\n"
            f.write(text)
        
        file_pickle = os.path.join(file_dir, "Parameter.txt")
        with open(file_pickle, "w") as f:
            text = f"====================================================\n\nPop Size = {self.popSize}\nMutation Rate = {self.mutationRate}\nElite Size = {self.eliteSize}\nGeneration = {self.itteration}\nTime Step = {self.timestep} Jam\n\n===================================================="
            f.write(text)

        plt.figure(0) 
        x = [i+1 for i in range(len(self.y_plot))]
        plt.plot(x, self.y_plot, label='Cost')
        plt.xlabel('Generation')
        plt.ylabel('Cost')
        plt.title("Training")
        plt.legend()
        file_pickle = os.path.join(file_dir, f"{file_name}.png")
        plt.savefig(file_pickle,bbox_inches='tight', transparent=True)

        file_pickle = os.path.join(file_dir, "Best Route Cost.csv")
        f = open(file_pickle,"w") 
        f.write(self.text)
        f.close()
        
        plt.figure(0)
        N = len(self.bar_char_data[0][1])
        max_val = 0
        ind = np.arange(N) 

        bar = []
        bottom = np.array([0 for i in range(N)])
        label = []
        for i in self.bar_char_data[1:]:
            label.append(i[0])
            val = np.array(i[1]) 
            bar.append(plt.bar(ind, val, 0.5, bottom=bottom))
            bottom = val + bottom
            max_val = max(max_val, np.max(bottom))
        
        max_val = max_val*1.3

        plt.xlabel('Nama Kapal')
        plt.ylabel('Cost')
        plt.ylim((0, max_val))
        plt.title("Cost Kapal")
        plt.xticks(ind, tuple(self.bar_char_data[0][1]))
        plt.legend(tuple(bar), tuple(label))

        file_pickle = os.path.join(file_dir, f"{file_name}_bar.png")
        plt.savefig(file_pickle,bbox_inches='tight', transparent=True)

        print("\nSaving Training Complete")
    def check_best_result(self):
        index = self.fitnessResults[0][0]

        obj = [ls.Kapal(self.pelabuhan, kpl["nama"], kpl["kategori"], kpl["kapasitas"],kpl["max_voyage"], kpl["rute"], kpl["speed"],kpl,self.timestep) for kpl in self.data["Kapal"]]
        for n,m in enumerate(self.pupulation_kapal[index]):
            rute_name = m.rute_name
            barg = m.full_rute_barang
            obj[n].add_rute(self.pelabuhan, (barg, rute_name))
        
        self.pupulation_kapal[index] = obj
        print("\nTest Overal Best Route")
        self.getFitness(index, mode="test")
        
        self.bar_char_data.append(["label", []])
        text = "Jenis Cost\t"
        for kpl in self.pupulation_kapal[index]:
            text += f"{kpl.nama} ({kpl.kategori})\t"
            self.bar_char_data[-1][1].append(f"{kpl.nama} ({kpl.kategori})")
        text += "\n"

        self.bar_char_data.append(["Travel Cost", []])
        text += "Travel Cost\t"
        for i in ((self.pupulation_kapal[index])):
            a = float(i.get_data()["travel_cost"])
            text += f"{a}\t"
            self.bar_char_data[-1][1].append(a)

        text += "\n"
        text += "Bongkar-Muat Cost\t"
        self.bar_char_data.append(["Bongkar-Muat Cost", []])
        for i in ((self.pupulation_kapal[index])):
            a = float(i.get_data()["bongkar_cost"])
            text += f"{a}\t"
            self.bar_char_data[-1][1].append(a)


        text += "\n"
        text += "Storage Cost\t"
        self.bar_char_data.append(["Storage Cost", []])
        for i in ((self.pupulation_kapal[index])):
            a = float(i.get_data()["storage_cost"])
            text += f"{a}\t"
            self.bar_char_data[-1][1].append(a)

        text += "\n"
        text += "Inventory Cost\t"
        self.bar_char_data.append(["Inventory Cost", []])
        for i in ((self.pupulation_kapal[index])):
            a = float(i.get_data()["inventory_cost"])
            text += f"{a}\t"
            self.bar_char_data[-1][1].append(a)

        text += "\n"
        text += "Total Cost\t"
        for i in ((self.pupulation_kapal[index])):
            a = float(i.get_data()["Total"])
            text += f"{a}\t"
        self.text = text