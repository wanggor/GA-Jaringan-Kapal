# -*- coding: utf-8 -*-
# Reading and Preprocessing Data
import re
import pandas as pd
from geopy import distance
import random

def mirroring(df): 
    df_c = df.copy()
    df = df.fillna(0)
    df = df + df.T
    df[df_c.isnull() & (df == 0)] = None
    return df

def set_same_zero(df):
    df_column = df.columns.values
    df_column = set(df_column)
    df_index = df.index.values
    df_index = set(df_index)
    same_port = df_index & df_column

    # making same port data into 0 
    for i in same_port:
        df[i][i]=0
    return df

def calculate_availibility(wave_status):
    wave_status['PR_availability'] = wave_status['wave_h']<2
    return wave_status

def fill_mean(df):
    df = df.fillna(df.mean().mean())
    return df

#Coordinate Data
def dms2dd(degrees, minutes, seconds, direction):
    dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
    if direction == 'W' or direction == 'S':
        dd *= -1
    return dd;

def dd2dms(deg):
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60
    return [d, m, sd]

def parse_dms(dms):
    parts = re.split('[°\'"]+', dms)
    lat = dms2dd(parts[0], parts[1], parts[2], parts[3])
    return lat

#Choosing and making port
def quickport(allport, ports, port_name):
    name = ports[ports['port'] == port_name]['port'].values[0]
    port_type = ports[ports['port'] == port_name]['port_type'].values[0]
    return Port(allport,name,port_type)

def chooseport(ports,port_name):
    port_name = port_name.rstrip()
    port_name = port_name.lstrip()
    return ports[ports['port'] == port_name]['port_object'].iloc[0]

def chooseship(ship_name):
    ship_name = ship_name.rstrip()
    ship_name = ship_name.lstrip()
    return ship_df[ship_df['Ship_Name'] == ship_name]['object'].iloc[0]

def add_TL_route(data, route):
    finished = False
    i = 0
    while finished == False:
        current_item = route[i]
        if current_item.name in ['Ambon','Saumlaki','Tual']:
            k=0
            for j in data["movable_TL"][current_item.name]:
                k+=1
                route.insert(i+k,j)
            i+=len(data["movable_TL"][current_item.name])
        i+=1
        if len(route) <= i:
            break
    return route

def port_items(all_port_item,port):
    item_list = all_port_item[all_port_item['Pelabuhan'] == port]
    return item_list

def find_distance(data, port_a,port_b):
#     print(port_a)
#     print(port_b)
    a = data["port_loc"][data["port_loc"]['Nama Pelabuhan'] == port_a]
    b = data["port_loc"][data["port_loc"]['Nama Pelabuhan'] == port_b]
#     print(a)
#     print(b)
#     print(a['Lat_decimal'].values[0])
#     print(a['Long_decimal'].values[0])
#     print(b['Lat_decimal'].values[0])
#     print(b['Long_decimal'].values[0])
    dist = distance.distance((a['Lat_decimal'].values[0],a['Long_decimal'].values[0]),(b['Lat_decimal'].values[0],b['Long_decimal'].values[0])).miles
    return dist

def choose_char(data, ship_type):
    if ship_type=='TL':
        ship_char = data["TL_char"]
    elif ship_type=='PL':
        ship_char = data["PL_char"]
    elif ship_type=='PR':
        ship_char = data["PR_char"]
    return ship_char

def per_item_revenue(biaya_jarak_teus,data):
#     distance = find_distance(data['Pelabuhan'],data['Tujuan Pelabuhan'])
    distance = data['Jarak']
    Bobot = data['Bobot']
    BJT = biaya_jarak_teus[data['Pelabuhan']][data['Tujuan Pelabuhan']]
#     BJT = biaya_jarak_teus[data['Pelabuhan Asal']][data['Tujuan Pelabuhan']]
    income = distance*Bobot*BJT
    return income

def port_revenue(data,storage_df):
    total_income = 0
    global gl, gli
    gl = storage_df
    for i in storage_df.index:
        gli = i
        income = per_item_revenue(data, storage_df.loc[i])
        total_income += income
    return total_income

def item_left(df):
    return int(df['Bobot'].sum())

def find_movable_port(ports, wave_status, special_PR,ship_type,port_name):
    if ship_type == 'TL':
        flag = False
    elif ship_type == 'PR':
        flag = True
    else:
        added_route = []
        return added_route
    r_list = special_PR[port_name].dropna().to_list()
    route_list = wave_status[wave_status['Port'].isin(r_list) & wave_status['PR_availability'] == flag]['Port'].to_list()
    added_route = []
    for i in route_list:
        added_route.append(chooseport(ports, i))
    return added_route

def all_item(available_ship,ports):
    itemdf = pd.DataFrame(columns = ['Pelabuhan','Bobot','Tujuan Pelabuhan','Jarak'])
    itemdf.index.name = 'code barang'
    for i in ports['port_object']:
        itemdf = itemdf.append(i.demand)
    for i in available_ship:
        itemdf = itemdf.append(i.storage)
    return itemdf

def create_route(ports, route_list):
    route = []
    for i in route_list:
        route.append(chooseport(ports, i))
    return route

def total_revenue(available_ship):
    total_revenue = 0
    for i in available_ship:
        total_revenue += i.revenue
    return total_revenue

def get_route(df):
    return df['Route'].to_list()

def create_ship_df(ports,special_PR, data, excel = 'Data Ship.xlsx'):
    x1 = pd.ExcelFile(excel)
    names = x1.sheet_names
    ship_df = pd.DataFrame()
    for i in names:
        ship_data = x1.parse(i)
        port_list = create_route(ports, get_route(ship_data))
        this_ship_df = pd.DataFrame(data = {'Ship_Name': [ship_data['Ship_Name'].iloc[0]],
                                           'Ship_Type': [ship_data['Ship_Type'].iloc[0]],
                                           'original_port': [ship_data['original_port'].iloc[0]],
                                            'object':[Ship(ship_data['Ship_Type'].iloc[0],
                                                               special_PR,ports,data,
                                                             route = port_list,
                                                             name=ship_data['Ship_Name'].iloc[0],
                                                             initial_port = ship_data['original_port'].iloc[0])]
                                           })
        ship_df = ship_df.append(this_ship_df)

    ship_df = ship_df.reset_index(drop=True)
    return ship_df

def adjust_wave(data):
    data["wave_status"]['wave_h'] = data["wave_status"]['wave_h'].apply(lambda x: random.random()*4)
    data["wave_status"] = calculate_availibility(data["wave_status"])
    data["movable_TL"] = {'Ambon'       : find_movable_port(data["ports"],data["wave_status"],data["special_PR"],'TL','Ambon'),
                          'Tual'        : find_movable_port(data["ports"],data["wave_status"],data["special_PR"],'TL','Tual'),
                          'Saumlaki'    : find_movable_port(data["ports"],data["wave_status"],data["special_PR"],'TL','Saumlaki')}
    data["route_PR_Ambon"] = [chooseport(data["ports"],'Ambon')]+find_movable_port(data["ports"],data["wave_status"],data["special_PR"],'PR','Ambon')
    data["route_PR_Tual"] = [chooseport(data["ports"],'Tual')]+find_movable_port(data["ports"],data["wave_status"],data["special_PR"],'PR','Tual')
    data["route_PR_Saumlaki"] = [chooseport(data["ports"], 'Saumlaki')]+find_movable_port(data["ports"],data["wave_status"],data["special_PR"],'PR','Saumlaki')
    return data

def shuffle_route(available_ship):
    for i in available_ship:
        random.shuffle(i.route)
    return available_ship
        
def initial_port_to_first(available_ship):
    for i in available_ship:
        init_index = i.route.index(i.initial_port)
        intial_port_to_front = i.route.pop(init_index)
        i.route.insert(0, intial_port_to_front)
    return available_ship
        
def redefine_route(data):
    data["ship_df"][(data["ship_df"]['Ship_Type'] == 'PR') & (data["ship_df"]['original_port'] == 'Ambon')]['object'].iloc[0].route = data["route_PR_Ambon"]
    data["ship_df"][(data["ship_df"]['Ship_Type'] == 'PR') & (data["ship_df"]['original_port'] == 'Tual')]['object'].iloc[0].route = data["route_PR_Tual"]
    data["ship_df"][(data["ship_df"]['Ship_Type'] == 'PR') & (data["ship_df"]['original_port'] == 'Saumlaki')]['object'].iloc[0].route = data["route_PR_Saumlaki"]

    for i in data["ship_df"][data["ship_df"]['Ship_Type'] == 'TL']['object'].to_list():
        i.route =  add_TL_route(data, i.route)
        
    return data

def port_sequence(data, ship):
    if ship.destination_dist<=ship.current_dist:
        ship.move_port()
        ship.move_storage()
        ship.find_destination()
        ship.destination_dist = find_distance(data, ship.destination.name, ship.current_port.name)
        ship.current_dist = 0
    elif ship.destination_dist>ship.current_dist:
        ship.storage['Jarak'] = ship.storage['Jarak']+ship.speed
        ship.current_dist+=ship.speed

def create_ports_object(all_port_item,ports):
    ports['port_object'] = ports['port'].apply(lambda x: quickport(all_port_item, ports,x))
    return ports

def refill_ports(ports):
    for i in ports['port_object'].to_list():
        i.demand = port_items(i.name)
        
def reset_revenue(available_ship):
    for i in available_ship:
        i.revenue = 0
    return available_ship

#CLASSES
class Port:
    def __init__(self,all_port_item, name,port_type):
        self.name = name
        self.port_type = port_type
        self.demand = port_items(all_port_item,name)
        
    
    def __repr__(self):
        if self.port_type == 'U':
            port_type_name = 'Utama'
        elif self.port_type == 'P':
            port_type_name = 'Pengumpul'
        elif self.port_type == 'R':
            port_type_name = 'Pengumpan'
        else:
            port_type_name = 'NOT DEFINED'

        return port_type_name + ":" + self.name
    

class Ship:
    def __init__(self, ship_type,special_PR,ports,data, route=[], name='No Name',initial_port = False,time_skip = 6):
        self.name = name
        self.ship_type = ship_type
        self.revenue = 0
        self.route = route
        self.current_port = route[0]
        
        self.data = data
        
        if initial_port == False:
            self.initial_port = route[0]
        else:
            self.initial_port = chooseport(ports,initial_port)
            
        self.port_cycle = route
        self.route_list = []
        self.ship_char = choose_char(data, self.ship_type)
        self.destination_dist = 0
        self.current_dist = 1000
        self.speed = self.ship_char['ship_char']['V']*time_skip
        self.max = self.ship_char['ship_char']['max_voyage']/(24/time_skip)
        for i in route:
            self.route_list.append(i.name)

        storage_df = pd.DataFrame(columns = ['Pelabuhan','Bobot','Tujuan Pelabuhan','Jarak'])
        storage_df.index.name = 'code barang'
        self.storage = storage_df
        self.storage_volume = storage_df['Bobot'].sum()
        
        #Capacity
        self.capacity = self.ship_char['ship_char']['VC']
        
        
        #special route for TL depending on wave height
        if self.ship_type == 'TL':
            self.TL_Special_PR = list(set(route).intersection(set(special_PR.columns))) #TODO : CHECK PR NOT IN AND IN BASED ON WAVE
            portcycle_name =[]
            for i in self.port_cycle:
                portcycle_name.append(i.name)
            P_port_PR_transitport =  list(set(portcycle_name).intersection(set(special_PR.columns)))
            P_port_non_PR_transitport = [x for x in special_PR.columns if x not in P_port_PR_transitport]
            
            self.PR_transitport = []
            self.non_PR_transitport = []

            for i in P_port_PR_transitport:
                self.PR_transitport.extend(special_PR[i].dropna().to_list())
            for i in P_port_non_PR_transitport:
                self.non_PR_transitport.extend(special_PR[i].dropna().to_list())

    def update_storage_volume(self):
        self.storage_volume = self.storage['Bobot'].sum()

    def cycle_list(self):
        self.port_cycle = list(self.port_cycle[1:])+[self.port_cycle[0]]

    def find_destination(self):
        pick_item = False

        i = 0
        while pick_item == False:
            if i < len(self.port_cycle):
                pick_item = self.simulate_moving()
                if pick_item == False:
                    self.cycle_list()
            else:
                return
            i += 1
        self.cycle_list()
        self.destination = self.port_cycle[0]
        return self.destination
    
    def move_port(self):
        self.current_port = self.port_cycle[0]

    def cost_per_item(self,item ):
        Bobot = item['Bobot']
        bm_time = self.ship_char[self.current_port.name ]['bm_time']
        C_bm = self.ship_char[self.current_port.name ]['C_bm']
        inventory_cost = self.ship_char[self.current_port.name ]['inventory_cost']
        bm_time = self.ship_char[self.current_port.name ]['bm_time']
        avg_docking_time = self.ship_char[self.current_port.name ]['avg_docking_time']
#         distance = find_distance(item['Pelabuhan'],self.current_port.name )
        distance = item['Jarak']
        V = self.ship_char['ship_char']['V']
        VC = self.ship_char['ship_char']['VC']
        port_storage_time = self.ship_char[self.current_port.name ]['port_storage_time']
        C_storage = self.ship_char[self.current_port.name ]['C_storage']

        total_cost_bongkar = Bobot*bm_time*C_bm
        total_cost_storage = Bobot * port_storage_time * C_storage
        total_cost_travel_time = inventory_cost*bm_time*(avg_docking_time*(distance/V))
        cost_bongkar_time = inventory_cost * (Bobot/C_bm)

        travel_cost = total_cost_bongkar + total_cost_storage+total_cost_travel_time+cost_bongkar_time
        
        return travel_cost, [total_cost_bongkar, total_cost_storage, total_cost_travel_time, cost_bongkar_time]
    
    def drop_off_item(self,tujuan_pelabuhan,finish_shipping = True):
        ship_item = self.storage[self.storage['Tujuan Pelabuhan'] == tujuan_pelabuhan]
        self.storage = pd.concat([self.storage, ship_item]).drop_duplicates(keep=False)
        
        if finish_shipping == False:
            ship_item['Pelabuhan'] = self.current_port.name
            self.current_port.demand = self.current_port.demand.append(ship_item)
#         elif finish_shipping == True:
#             self.revenue += port_revenue(ship_item)
        
        #CALCULATING SHIP COST        
        total_cost_bongkar = 0
        total_cost_storage = 0
        total_cost_travel_time = 0
        cost_bongkar_time = 0
        travel_cost = 0
        for i in list(ship_item.index):
            item = ship_item.loc[i]
            travel_cost,_ = self.cost_per_item(item)
        self.revenue -= travel_cost
        self.revenue += port_revenue(self.data["Biaya_Jarak_Teus"],ship_item)

        self.update_storage_volume()
            
        return ship_item
    
    def pick_up_each(self,port_item):
        for i in port_item.index:
            current_port_item = port_item.loc[i]
            bobot_item = current_port_item['Bobot']
            if (self.storage_volume + bobot_item)<=self.capacity:
                bobot_item_df = pd.DataFrame(current_port_item).T
                self.current_port.demand = pd.concat([self.current_port.demand, bobot_item_df]).drop_duplicates(keep=False)
                bobot_item_df['Jarak'] = 0
                self.storage = self.storage.append(bobot_item_df)
                self.update_storage_volume()    
    
    def pick_up_port(self,tujuan_pelabuhan):
        port_item = self.current_port.demand[self.current_port.demand['Tujuan Pelabuhan'] == tujuan_pelabuhan]
        self.pick_up_each(port_item)

    def check_item(self,tujuan_pelabuhan,pick_or_drop,pick_item=False):
        if pick_item == True:
            return pick_item
        else:
            if pick_or_drop == 'drop':
                ship_item = self.storage[self.storage['Tujuan Pelabuhan'] == tujuan_pelabuhan]
                pick_item = not(ship_item.empty)
            elif pick_or_drop == 'pick':
                port_item = self.port_cycle[1].demand[self.port_cycle[1].demand['Tujuan Pelabuhan'] == tujuan_pelabuhan]
                pick_item = not(port_item.empty)
            return pick_item
    
    def simulate_moving(self):
        # ITEM DROP OFF--------------------------------------------------------
        simulated_port = self.port_cycle[1]
        # ALL ITEM WITH PORT DESTINATION AT CURRENT PORT
        pick_item = False
        pick_item = self.check_item(simulated_port.name,'drop',pick_item=pick_item)

        #SPECIAL DROP OFF ITEM
        #FOR PR
        if self.ship_type == 'PR':
            if simulated_port.name not in self.data["R_list"]:
                for i in self.data["ports"][~self.data["ports"]['port'].isin(self.route)]['port'].to_list():
                    pick_item = self.check_item(i,'drop',pick_item=pick_item)
        

        #for Tanjung Perak and Makassar
        if simulated_port.name in ['Tanjung Perak','Makassar']:            
            #FOR TL
            if self.ship_type == 'TL':
                pick_item = self.check_item('Tanjung Priok','drop',pick_item=pick_item)
                P_non_in_route = [x for x in self.data["ports"][self.data["ports"]['port_type'] == 'P']['port'].to_list() if x not in self.route]
                U_non_in_route = [x for x in self.data["ports"][self.data["ports"]['port_type'] == 'U']['port'].to_list() if x not in self.route]
                for i in self.non_PR_transitport:
                    pick_item = self.check_item(i,'drop',pick_item=pick_item)
                for i in P_non_in_route:
                    pick_item = self.check_item(i,'drop',pick_item=pick_item)
                for i in U_non_in_route:
                    pick_item = self.check_item(i,'drop',pick_item=pick_item)
            #FOR PL
            elif self.ship_type == 'PL':
                not_in_route = [x for x in self.data["ports"]['port'].to_list() if x not in self.route]
                for i in not_in_route:
                    pick_item = self.check_item(i,'drop',pick_item=pick_item)

       #for Special PR (Ambon, Tual, and Saumlaki)
        if simulated_port.name in self.data["special_PR"].columns:
            #FOR PL
            if self.ship_type == 'PL':
                current_port_R_ports = self.data["special_PR"][simulated_port.name].dropna().to_list()                
                for i in current_port_R_ports:
                    pick_item = self.check_item(i,'drop',pick_item=pick_item)
            #FOR TL
            elif self.ship_type == 'TL':
                current_r = find_movable_port(self.data["ports"], self.data["wave_status"], self.data["special_PR"],'PR',simulated_port.name)
                for i in current_r:
                    pick_item = self.check_item(i.name,'drop',pick_item=pick_item)
        # ITEM DROP OFF--------------------------------------------------------

        
        
        
        # ITEM PICK UP--------------------------------------------------------
        
        #PICK UP IN PORT CYCLE
        for i in self.port_cycle:
            pick_item = self.check_item(i.name,'pick',pick_item=pick_item)

        #Take for Tanjung Priok
        if self.ship_type == 'TL':
            if self.current_port.name not in ['Tanjung Perak','Makassar']:
                self.check_item('Tanjung Priok','pick',pick_item=pick_item)
        if self.ship_type == 'PR':
            if self.current_port.name not in self.data["special_PR"].columns:
                self.check_item('Tanjung Priok','pick',pick_item=pick_item)
            
        #SPECIAL FOR PL SHIP: 
        if self.ship_type == 'PL':
            #TAKE EVERYTHING with TANJUNG PRIOK
            self.pick_up_port('Tanjung Priok')
            if simulated_port.name not in self.data["special_PR"].columns:
                for i in self.data["R_list"]:
                    pick_item = self.check_item(i,'pick',pick_item=pick_item)

            #TAKE EVERYTHING in BANDA NEIRA
            if self.current_port.name == 'Banda Neira':
                port_item = self.current_port.demand
                if pick_item == True:
                    pass
                else:
                    pick_item = not(port_item.empty)
                    
#         P not in special P
        if ((simulated_port.port_type == 'P') and (simulated_port.name not in self.data["special_PR"].columns)):
            if self.ship_type == 'TL':
                for i in self.PR_transitport:
                    pick_item = self.check_item(i,'pick',pick_item=pick_item)


        #for Tanjung Priok
        if simulated_port.name == 'Tanjung Priok':
            if self.ship_type == 'PL':
                port_item = simulated_port.demand
                pick_item = self.check_item(i,'pick',pick_item=pick_item)
                
            
        #for Tanjung Perak and Makassar
        if simulated_port.name in ['Tanjung Perak','Makassar']:
            #FOR TL
            if self.ship_type == 'TL':
                for i in list(set(self.data["special_PR"].columns) & set(self.route_list)):
                    i_r_list = find_movable_port(self.data["ports"], self.data["wave_status"], self.data["special_PR"],self.ship_type,i)
                    for j in i_r_list:
                        pick_item = self.check_item(j,'pick',pick_item=pick_item)     
            elif self.ship_type == 'PL':
                pick_item = self.check_item(i,'pick',pick_item=pick_item)

        #for Special PR
        if simulated_port.name in self.data["special_PR"].columns:
            #FOR TL
            if self.ship_type == 'TL':
                port_PR_ports = find_movable_port(self.data["ports"], self.data["wave_status"], self.data["special_PR"],'TL',simulated_port.name)
                special_pr_ports_list = self.data["special_PR"].columns.to_list()
                special_pr_ports_list.remove(simulated_port.name)
                other_r_list = []
                for i in special_pr_ports_list:
                    other_r_list.extend(self.data["special_PR"][i].dropna().to_list())
                port_PR_ports.extend(other_r_list)
                for i in port_PR_ports:
                    pick_item = self.check_item(i,'pick',pick_item=pick_item)
                
            #FOR PR
            elif self.ship_type == 'PR':
                port_PR_ports = find_movable_port(self.data["ports"], self.data["wave_status"], self.data["special_PR"],'PR',simulated_port.name)
                for i in port_PR_ports:
                    pick_item = self.check_item(i,'pick',pick_item=pick_item)

        #for R
        if simulated_port.name in self.data["R_list"]+['Banda Neira']:
            port_item = simulated_port.demand
            pick_item = self.check_item(i,'pick',pick_item=pick_item) #TODO 

            if pick_item == True:
                pass
            else:
                pick_item = not(port_item.empty)

            
        # ITEM PICK UP--------------------------------------------------------
        return pick_item
    
    def move_storage(self):
        # ITEM DROP OFF--------------------------------------------------------
        
        # ALL ITEM WITH PORT DESTINATION AT CURRENT PORT
        self.drop_off_item(self.current_port.name)
        
        #SPECIAL DROP OFF ITEM
        #FOR PR
        if self.ship_type == 'PR':
            if self.current_port.name not in self.data["R_list"]:
                for i in self.data["ports"][~self.data["ports"]['port'].isin(self.route)]['port'].to_list():
                    self.drop_off_item(i,finish_shipping = False)
        
        #for Tanjung Perak and Makassar
        if self.current_port.name in ['Tanjung Perak','Makassar']:
            
            #FOR TL
            if self.ship_type == 'TL':
                self.drop_off_item('Tanjung Priok',finish_shipping = False )
                P_non_in_route = [x for x in self.data["ports"][self.data["ports"]['port_type'] == 'P']['port'].to_list() if x not in self.route]
                U_non_in_route = [x for x in self.data["ports"][self.data["ports"]['port_type'] == 'U']['port'].to_list() if x not in self.route]
                for i in self.non_PR_transitport:
                    self.drop_off_item(i,finish_shipping = False )
                for i in P_non_in_route:
                    self.drop_off_item(i,finish_shipping = False)
                for i in U_non_in_route:
                    self.drop_off_item(i,finish_shipping = False)

            #FOR PL
            elif self.ship_type == 'PL':
                not_in_route = [x for x in self.data["ports"]['port'].to_list() if x not in self.route]
                for i in not_in_route:
                    self.drop_off_item(i,finish_shipping = False )

       #for Special PR (Ambon, Tual, and Saumlaki)
        if self.current_port.name in self.data["special_PR"].columns:
            #FOR PL
            if self.ship_type == 'PL':
                current_port_R_ports = self.data["special_PR"][self.current_port.name].dropna().to_list() 
                for i in current_port_R_ports:
                    self.drop_off_item(i.strip(),finish_shipping = False)
            #FOR TL
            elif self.ship_type == 'TL':
                current_r = find_movable_port(self.data["ports"], self.data["wave_status"], self.data["special_PR"],'PR',self.current_port.name)
                for i in current_r:
                    self.drop_off_item(i.name,finish_shipping = False)
                    
        self.current_port.demand = self.current_port.demand.loc[~self.current_port.demand.index.duplicated(keep='first')]
        # ITEM DROP OFF--------------------------------------------------------

        
        
        
        # ITEM PICK UP--------------------------------------------------------
        
        #PICK UP IN PORT CYCLE
        for i in self.port_cycle:
            self.pick_up_port(i.name)
        
        #Take for Tanjung Priok
        if self.ship_type == 'TL':
            if self.current_port.name not in ['Tanjung Perak','Makassar']:
                self.pick_up_port('Tanjung Priok')
        if self.ship_type == 'PR':
            if self.current_port.name not in self.data["special_PR"].columns:
                self.pick_up_port('Tanjung Priok')
            
        #SPECIAL FOR PL SHIP: 
        if self.ship_type == 'PL':
            #TAKE EVERYTHING with TANJUNG PRIOK
            self.pick_up_port('Tanjung Priok')
            if self.current_port.name not in self.data["special_PR"].columns:
                for i in self.data["R_list"]:
                    self.pick_up_port(i)
                    
            #TAKE EVERYTHING in BANDA NEIRA
            if self.current_port.name == 'Banda Neira':
                port_item = self.current_port.demand
                self.pick_up_each(port_item)   
                
#         P not in special P
        if ((self.current_port.port_type == 'P') and (self.current_port.name not in self.data["special_PR"].columns)):
            if self.ship_type == 'TL':
                for i in self.PR_transitport:
                    self.pick_up_port(i)


        #for Tanjung Priok
        if self.current_port.name == 'Tanjung Priok':
            if self.ship_type == 'PL':
                port_item = self.current_port.demand
                self.pick_up_each(port_item)
                
            
        #for Tanjung Perak and Makassar
        if self.current_port.name in ['Tanjung Perak','Makassar']:
            #FOR TL
            if self.ship_type == 'TL':
                for i in list(set(self.data["special_PR"].columns) & set(self.route_list)):
                    i_r_list = find_movable_port(self.data["ports"],self.data["wave_status"],self.data["special_PR"],self.ship_type,i)
                    for j in i_r_list:
                        self.pick_up_port(j)     
            elif self.ship_type == 'PL':
                self.pick_up_port('Tanjung Priok')

        #for Special PR
        if self.current_port.name in self.data["special_PR"].columns:
            #FOR TL
            if self.ship_type == 'TL':
                port_PR_ports = find_movable_port(self.data["ports"], self.data["wave_status"], self.data["special_PR"],'TL',self.current_port.name)
                special_pr_ports_list = self.data["special_PR"].columns.to_list()
                special_pr_ports_list.remove(self.current_port.name)
                other_r_list = []
                for i in special_pr_ports_list:
                    other_r_list.extend(self.data["special_PR"][i].dropna().to_list())
                port_PR_ports.extend(other_r_list)
                for i in port_PR_ports:
                    self.pick_up_port(i)
                
            #FOR PR
            elif self.ship_type == 'PR':
                port_PR_ports = find_movable_port(self.data["ports"], self.data["wave_status"], self.data["special_PR"],'PR',self.current_port.name)
                for i in port_PR_ports:
                    self.pick_up_port(i)

        #for R
        if self.current_port.name in self.data["R_list"]+['Banda Neira']:
            port_item = self.current_port.demand
            self.pick_up_each(port_item)

        self.storage = self.storage.loc[~self.storage.index.duplicated(keep='first')]
        self.storage['Jarak'] = self.storage['Jarak'].fillna(0)

        # ITEM PICK UP--------------------------------------------------------
      
    
    
    
    def __repr__(self):
        return self.name +': '+ self.ship_type