# -*- coding: utf-8 -*-
import pandas as pd
import training_utils as tu
import numpy as np
import operator
import random
import time
import matplotlib.pyplot as plt

path = "Data.xlsx"
excel = pd.ExcelFile(path)

data = {}
for sheet_name in excel.sheet_names:
    if sheet_name in ["special_PR","wave_status","ports","port_loc"]:
        data[sheet_name] = excel.parse(sheet_name).applymap(lambda x: x.strip() if isinstance(x, str) else x)
    else: 
       data[sheet_name] = excel.parse(sheet_name, index_col=0).applymap(lambda x: x.strip() if isinstance(x, str) else x)

data["R_list"] = data["ports"][data["ports"]['port_type'] == 'R']['port'].to_list()
data["P_list"] = data["ports"][data["ports"]['port_type'] == 'P']['port'].to_list()
data["PL_P_list"] = ['Banda Neira','Dobo','Ambon','Tual','Saumlaki']
data["PL_non_P_list"] = list(set(data["P_list"])-set(data["PL_P_list"]))

data["special_P_port"] = data["special_PR"].columns.to_list()
data["wave_status"]['PR_availability'] = data["wave_status"]["wave_h"]<2

data["Ambon_R_list"] = data["special_PR"]['Ambon'].dropna().to_list()
data["Tual_R_list"] = data["special_PR"]['Tual'].dropna().to_list()
data["Saumlaki_R_list"] = data["special_PR"]['Saumlaki'].dropna().to_list()   

data["Biaya_Jarak_Teus"] = tu.fill_mean(data["Biaya_Jarak_Teus"])
data["TL_char"] = tu.fill_mean(data["TL_char"])
data["PL_char"] = tu.fill_mean(data["PL_char"])
data["PR_char"] = tu.fill_mean(data["PR_char"])

data["port_loc"]['Lat_decimal'] = data["port_loc"]['Latitude'].apply(tu.parse_dms)
data["port_loc"]['Long_decimal'] = data["port_loc"]['Longitude'].apply(tu.parse_dms)

data["all_port_item"] = data["barang_dummy_small"]
data["port_item"] = data["Barang"]

data["ports"] = tu.create_ports_object(data["all_port_item"],data["ports"])

time_skip = 6

data["ship_df"] = tu.create_ship_df(data["ports"],data["special_PR"],data,'Data Ship.xlsx')
data["available_ship"] = data["ship_df"]['object'].to_list()

data["available_ship"] = data["available_ship"][-1:]
data = tu.adjust_wave(data)
data = tu.redefine_route(data)
data["available_ship"] = tu.shuffle_route(data["available_ship"])
data["available_ship"] = tu.initial_port_to_first(data["available_ship"])

print_progress = True

def simulate_fitness(data,available_ship, print_progress = False, print_report = False):    
    new_port_item = tu.all_item(available_ship,data["ports"])
    remaining = tu.item_left(new_port_item)
    i=0
    remaining_history = []
    revenue_history = []
    tic = time.clock()

    while remaining>0:
        i +=1
        for ship in available_ship:
            tu.port_sequence(data, ship)
#        print('{} revenue: {}'.format(ship.name,ship.revenue))
        new_port_item = tu.all_item(available_ship,data["ports"])
        remaining = tu.item_left(new_port_item)
        revenue = tu.total_revenue(available_ship)
        if print_progress == True:
            print('************************************************')
            print('revenue: {}'.format(revenue))
            print('remaining: ' + str(remaining))
            print('iteration: ' + str(i))
            print('************************************************')
        remaining_history.append(remaining)
        revenue_history.append(revenue)
        if i>=7000:
            break
    if print_report == True:
        print('************************************************')
        print('************************************************')
        print('revenue: {}'.format(revenue))
        print('remaining: ' + str(remaining))
        print('iteration: ' + str(i))
        print('************************************************')
        print('************************************************')
        
    toc = time.clock()
    processtime = toc-tic
    print('process time:{}'.format(processtime))
    return revenue,remaining_history,revenue_history,processtime

def initial_population(data, ship_names, n_pop):
    pop = []
    for i in range(n_pop):
        individual = {}
        for j in ship_names:
            route = tu.chooseship(data, j).route.copy()
            for r_i in range(int(np.random.uniform(15,0))+1):
                random.shuffle(route)
            init_index = route.index(tu.chooseship(data, j).initial_port)
            intial_port_to_front =route.pop(init_index)
            route.insert(0, intial_port_to_front)
            individual[j] = route
        pop.append(individual)
    return pop

def change_ship_route(data, individual):
    for i in list(individual.keys()):
        tu.chooseship(data,i).route = individual[i]
        
def analyse_simulation(remaining_history,revenue_history):
    plt.plot(remaining_history)
    plt.show()
    plt.plot(revenue_history)
    plt.show()
    print('Total Revenue: {}'.format(revenue_history[-1]))
        
def rankRoutes(data, population,available_ship,ports,print_progress_flag = True):
    fitnessResults = {}
    for i in range(0,len(population)):
        tu.refill_ports(data,data["ports"])
        print('*********POPULATION {}***********'.format(i))
        available_ship = tu.reset_revenue(available_ship)
        change_ship_route(data, population[i])
        fitnessResults[i],remaining_history,revenue_history,processtime = simulate_fitness(data,available_ship, print_progress = True)
        analyse_simulation(remaining_history,revenue_history)
    return sorted(fitnessResults.items(), key = operator.itemgetter(1), reverse = True)

def selection(popRanked, eliteSize):
    selectionResults = []
    df = pd.DataFrame(np.array(popRanked), columns=["Index","Revenue"])
    df['cum_sum'] = df.Revenue.cumsum()
    df['cum_perc'] = 100*df.cum_sum/df.Revenue.sum()
    
    for i in range(0, eliteSize):
        selectionResults.append(popRanked[i][0])
    for i in range(0, len(popRanked) - eliteSize):
        pick = 100*random.random()
        for i in range(0, len(popRanked)):
            if pick <= df.iat[i,3]:
                selectionResults.append(popRanked[i][0])
                break
    return selectionResults

def matingPool(population, selectionResults):
    matingpool = []
    for i in range(0, len(selectionResults)):
        index = selectionResults[i]
        matingpool.append(population[index])
    return matingpool

def breed(parent1,parent2):
    childP1 = parent1.copy()
    childP2 = parent2.copy()

    key = list(childP1.keys())

    flags = []
    for i in range(len(parent1)):
        flags.append(bool(random.getrandbits(1)))

    for i in range(len(flags)):
        if flags[i] == True:
            childP1[key[i]],childP2[key[i]] = childP2[key[i]],childP1[key[i]]

    child = random.choice([childP1,childP2])
    return child

def breedPopulation(matingpool, eliteSize):
    children = []
    length = len(matingpool) - eliteSize
    pool = random.sample(matingpool, len(matingpool))

    for i in range(0,eliteSize):
        children.append(matingpool[i])
    
    for i in range(0, length):
        child = breed(pool[i], pool[len(matingpool)-i-1])
        children.append(child)
    return children

def mutate(individual, mutationRate):
    for i in list(individual.keys()):
        ind_ship = individual[i]
        for swapped in range(1,len(ind_ship)):
            if(random.random() < mutationRate):
                swapWith = int(random.random() * (len(ind_ship)-1))+1

                port1 = ind_ship[swapped]
                port2 = ind_ship[swapWith]

                ind_ship[swapped] = port2
                ind_ship[swapWith] = port1
                
    return individual

def mutatePopulation(population, mutationRate):
    mutatedPop = []
    
    for ind in range(0, len(population)):
        mutatedInd = mutate(population[ind], mutationRate)
        mutatedPop.append(mutatedInd)
    return mutatedPop

def nextGeneration(data, currentGen,popRanked,eliteSize, mutationRate,available_ship,ports,print_progress=False):
#     popRanked = rankRoutes(currentGen,available_ship,ports,print_progress_flag = True)
    selectionResults = selection(popRanked, eliteSize)
    matingpool = matingPool(currentGen, selectionResults)
    children = breedPopulation(matingpool, eliteSize)
    nextGeneration = mutatePopulation(children, mutationRate)
    popRanked = rankRoutes(data, nextGeneration,available_ship,ports,print_progress_flag = print_progress)
    return nextGeneration, popRanked

def geneticAlgorithmPlot(data, ship_names, popSize, eliteSize, mutationRate, generations):

    progress = []
    best_progress = []
    available_ship = []
    
    for i in ship_names:
        available_ship.append(tu.chooseship(data, i))

    pop = initial_population(data, ship_names, popSize)    
    initial_rank = rankRoutes(data, pop,available_ship,data["ports"],print_progress_flag = False)
    pop_rank = initial_rank
    
    print('********************************************************')
    print("Initial BEST Revenue: " + str(initial_rank[0][1]))
    print('********************************************************')


    best_route_overall = pop[initial_rank[0][0]]
    best_gene_dist = initial_rank[0][1]
    
    progress.append(initial_rank[0][1])
    best_progress.append(initial_rank[0][1])
    
    for i in range(0, generations):
        tic = time.clock()
        print('********************************************************')
        print('******************* GENERATION {} **********************'.format(i+1))
        print('********************************************************')
        
        pop, pop_rank= nextGeneration(data, pop,pop_rank, eliteSize, mutationRate,available_ship,data["ports"])
#         pop_rank = rankRoutes(pop,available_ship,ports,print_progress_flag = False)

        if (pop_rank[0][1]) > best_gene_dist : 
            best_gene_dist = (pop_rank[0][1])
            best_route_overall = pop[pop_rank[0][0]]
          
        
        best_progress.append(best_gene_dist)
        progress.append(pop_rank[0][1])

        
        
        print('iteration: ' + str(i+1) + ' current best revenue: ' + str(pop_rank[0][1]) + ' overall best revenue: ' + str(best_gene_dist)) 
        toc = time.clock()
        generation_time = toc-tic
        print('process time for generation : {}'.format(generation_time))
    print("Final Revenue: " + str(pop_rank[0][1]))
    
        
    bestRouteIndex = pop_rank[0][0]
    bestRoute = pop[bestRouteIndex]
    
    
    plt.plot(best_progress)
    plt.plot(progress)
    plt.ylabel('Revenue')
    plt.xlabel('Generation')
    plt.show()
    
    return bestRoute,best_route_overall,progress,best_progress


ship_names = data["ship_df"]['Ship_Name'].to_list()
n_pop = 8
elite_n = 3
mutationRate = 0.00005
n_generation = 10
pop = initial_population(data, ship_names, n_pop)

bestRoute,best_route_overall,progress,best_progress = geneticAlgorithmPlot(data, ship_names, n_pop, elite_n, mutationRate, n_generation)

