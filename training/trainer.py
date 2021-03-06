from utils import preprocessing, geopath
from models import logistic_models as ls
import random
import operator
import pandas as pd
import numpy as np

class GA_Trainer():
    def __init__(self, path_data, path_ship, popSize, eliteSize, mutationRate, timestep = 0.1, draw = False):
        self.popSize = popSize
        self.eliteSize = eliteSize
        self.mutationRate = mutationRate
        
        self.draw = draw
        self.timestep = timestep
        self.path = [path_data,path_ship]
        self.data = preprocessing.parsing_data_2(self.path)
        self.original_port = { i["nama"]: [i["kategori"],i["rute"][0]]for i in self.data["Kapal"]}
        self.createPelabuhan()
        self.p = 0

    def createPelabuhan(self):
        self.pelabuhan = ls.JaringanPelabuhan()
        self.pelabuhan.add_multiPelabuhan(self.data["Daftar Pelabuhan"])
        self.pelabuhan.add_rute_from_lis(self.data["Rute"])
        self.pelabuhan.add_barang(self.data["Barang"])
        # self.pelabuhan.add_transit(self.data)
        self.pelabuhan.add_transit_cluster(self.data)
        self.Total_Nilai_Harga, self.data["Barang"] = self.pelabuhan.add_Harga(self.data["Harga Barang"], self.data["Daftar Pelabuhan"], self.data["Barang"])

        
        
    def initialPopulation(self, popSize):
        self.pupulation_kapal = []
        for i in range(0, popSize):
            self.pupulation_kapal.append(self.createObjectKapal())

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
        obj = [ls.Kapal(self.pelabuhan, kpl["nama"], kpl["kategori"], kpl["kapasitas"], kpl["rute"], kpl["speed"],kpl,self.timestep) for kpl in self.data["Kapal"]]

        # self.data_kode_barang = self.pelabuhan.get_rute_barang3(self.data["port"],self.original_port, self.data["Daftar Pelabuhan"],obj)
        data_kode_barang = self.pelabuhan.get_rute_barang(self.data["port"],self.original_port, self.data["Daftar Pelabuhan"])
        for kpl in obj:
                original_port = kpl.rute_name[0]
                if kpl.kategori in ["TL", "PL"]:
                    kpl.add_rute(self.pelabuhan,self.random_route(data_kode_barang["Jarak Jauh"],original_port))
                else:
                    route = self.choose_route(data_kode_barang["Jarak Dekat"], self.data["Spesial PR"], original_port)
                    kpl.add_rute(self.pelabuhan,route)
                    
                    # kpl.add_rute(self.pelabuhan,self.random_route(data_kode_barang["Jarak Dekat"],original_port)) 
        return obj

    def random_route(self,data,original):
        output = [original]
        for i in data:
            for j in data[i]:
                if j not in output:
                    output.append(j)
        output.remove(original)
        random.shuffle(output)
        return data, [original]+output
    
    def getFitness(self, index):
        self.createPelabuhan()
        n = 0
        sisa = 1
        [i.reset(self.pelabuhan) for i in self.pupulation_kapal[index]]
        
        while True:
            n += 1
            [i.update(self.pelabuhan) for i in self.pupulation_kapal[index]]
            self.pelabuhan.checking_posisi(self.pupulation_kapal[index])
            
            total = sum([float(i["Bobot"]) for i in self.data["Barang"]])
            cost = sum([ float(i.get_data()["Total"]) for i in self.pupulation_kapal[index]])
            sisa = sum([ float(i["Total"]) for i in self.pelabuhan.get_barang()])
            revenue = sum([ float(i["Bobot"]) for i in self.pelabuhan.get_barang_sampai()])
            beban_kapal = sum([ float(i.beban_angkut) for i in self.pupulation_kapal[index]])
            transit = sum([ float(i["Total"]) for i in self.pelabuhan.get_barang_transit()])
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
            if (beban_kapal <= 0) and (sisa <= 0) and (transit <= 0):
                break
        return int(cost)
    
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
            obj = [ls.Kapal(self.pelabuhan, kpl["nama"], kpl["kategori"], kpl["kapasitas"], kpl["rute"], kpl["speed"],kpl,self.timestep) for kpl in self.data["Kapal"]]
            for n,m in enumerate(self.matingpool[i]):
                rute_name = m.rute_name
                barg = m.full_rute_barang
                obj[n].add_rute(self.pelabuhan, (barg, rute_name))
            children.append(obj)
            
        self.pool = random.sample(self.matingpool, len(self.matingpool))

        for i in range(0, length):
            child = self.pelabuhan.breed2(self.pool[i], self.pool[len(self.matingpool)-i-1])
            obj = [ls.Kapal(self.pelabuhan, kpl["nama"], kpl["kategori"], kpl["kapasitas"], kpl["rute"], kpl["speed"],kpl,self.timestep) for kpl in self.data["Kapal"]]
            for i in range(len(child)):
                obj[i].add_rute(self.pelabuhan, child[i])
            children.append(obj)
        self.pupulation_kapal = children

        
    
    def mutate(self,  individual, mutationRate):
        for i in individual:
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
            self.mutate(self.pupulation_kapal[ind], mutationRate)

    def nextGeneration(self):
        self.rankRoutes()
        self.selection(self.eliteSize)#eliteSize
        self.matingPool()
        self.breedPopulation(self.eliteSize)
        self.mutatePopulation(self.mutationRate)
        
        return self.fitnessResults[0][1]

    def extract_best_route(self):
        bestRouteIndex =self.fitnessResults[0][0]
        bestRoute = self.pupulation_kapal[bestRouteIndex]
        return bestRoute