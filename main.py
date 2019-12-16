# -*- coding: utf-8 -*-
"""
Created on Tue Oct 22 19:15:12 2019

@author: wahyu anggoro (anggorow9@gmail.com)
"""
from PyQt5.QtWidgets import QApplication,QMainWindow,QStyleFactory,QVBoxLayout,QFileDialog,QMessageBox
from PyQt5 import uic, QtWidgets
from PyQt5.QtCore import QTimer,pyqtSlot,QDateTime
from pyqtlet import L, MapWidget
import pyqtgraph as pg
import pyqtgraph.exporters
import sys

from os import listdir
from os.path import isfile, join, exists
import os

from models import logistic_models as ls
from utils import preprocessing as pr, widget_utils as wu
from gui import plotWidget
from training import train
from utils.color_picker import MplColorHelper

import random
import pickle

def random_route(data,original, port_list):
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

class Main(QMainWindow):
    def __init__(self):
        super(Main, self).__init__()
        self.ui = uic.loadUi('gui/interface.ui',self)
        
        self.pelabuhan = ls.JaringanPelabuhan()
               
        self.data = None
        self.train_thread = None
        self.object_kapal = None
        self.date = None
        self.path = []
        self.setup()
    
    def setup(self):
        self.ui.layout_main_view = QVBoxLayout(self.ui.frame1)
        self.mapWidget = MapWidget()
        self.ui.layout_main_view.addWidget(self.mapWidget)
        
        self.ui.listWidget.scrollToBottom()
        self.ui.widget_3.hide()
        self.ui.pushButton_download.hide()
        self.ui.frame_4.hide()
        self.ui.listWidget_rute.hide()
        self.ui.pushButton_reset.hide()

        self.ui.dateTimeEdit.setEnabled(False)
        self.ui.dateTimeEdit_2.setEnabled(False)

        self.ui.pushButton_load.clicked.connect(self.file_dialog)
        self.ui.pushButton_start_simulasi.clicked.connect(self.start_simulation)
        self.ui.pushButton_training.clicked.connect(self.start_training)
        self.ui.pushButton_save.clicked.connect(self.save)
#        self.ui.pushButton_download.clicked.connect(self.download)
        self.ui.pushButton_cuaca.clicked.connect(self.perubahan_cuaca)
        self.ui.pushButton_reset.clicked.connect(self.reset)

        self.tabWidget.removeTab(1)
        
        self.ui.pushButton_Initialize.clicked.connect(self.initialize_training)
        
        self.ui.plot = plotWidget.LineGraph("Training")
        self.train_layout = QVBoxLayout(self.ui.widget_graph)
        self.train_layout.addWidget(self.ui.plot.widget)

        #COBA
        self.ui.pushButton_start_simulasi.setEnabled(True)
        
        # Working with the maps with pyqtlet
        self.map = L.map(self.mapWidget)
        self.map.setView([-4.135743, 118.002626], 5)
        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.map)
        
        self.timer1 = QTimer(self)
        self.timer1.timeout.connect(self.update)
        
        self.layer_cuaca = {}
        self.wave_count = 0
        self.data_wave = []

        self.picker = MplColorHelper("jet", 0,8)
        self.n = 0
        
    def perubahan_cuaca(self, name_pel):
        # name_pel = self.ui.comboBox_pelabuhan.currentText()
        obj = self.pelabuhan.lis_pelabuhan[name_pel.strip()]
        posisi = obj.posisi
        obj.is_high = not obj.is_high
        if obj.is_high:
            options= "{color : '#fc9d03', radius: 20, fillOpacity:0.2}"
            self.layer_cuaca[name_pel] = L.circleMarker(posisi,options= options)
            self.layer_cuaca[name_pel].bindTooltip(name_pel.capitalize())
            self.map.addLayer(self.layer_cuaca[name_pel])
        else:
            self.map.removeLayer(self.layer_cuaca[name_pel])
                
    
    def initialize_training(self):
        self.ui.listWidget.clear()
        if self.train_thread is None:
            paramerer = {}
            paramerer["Mutation Rate"] = float(self.ui.lineEdit_mutation.text())
            paramerer["Generations"] = int(self.ui.lineEdit_generation.text())
            paramerer["popSize"] = int(self.ui.lineEdit_popSizes.text())
            paramerer["eliteSize"] = int(self.ui.lineEdit_eliteSize.text())
            paramerer["path"] = self.path
            
            self.train_thread = train.Train(paramerer,parent = self)
            self.train_thread.data.connect(self.train_report)
            
            self.pushButton_training.setEnabled(True)
            self.ui.pushButton_Initialize.setEnabled(False)
            
            
    def start_training(self):
        if self.train_thread is not None:
            if self.ui.pushButton_training.text() == "Mulai Training":
                self.train_thread.start()
                self.pushButton_training.setEnabled(False)
                self.ui.pushButton_training.setText("Stop Training")
                self.ui.pushButton_Initialize.setEnabled(False)
            
            else:
                self.train_thread.stop()
                self.ui.pushButton_training.setText("Mulai Training")
                self.pushButton_training.setEnabled(False)
                self.ui.pushButton_Initialize.setEnabled(True)
    @pyqtSlot(dict)
    def train_report(self,data):
        if "y" in data.keys():
            self.ui.plot.update(data)
            self.ui.listWidget.addItem(str(data["msg"]))
            self.pushButton_training.setEnabled(True)
                
        if "Kapal" in data.keys():
            self.object_kapal = data["Kapal"]
            
            for kpl in self.object_kapal:
                separator = QtWidgets.QFrame()
                separator.setFrameShape(QtWidgets.QFrame.HLine)
                separator.setLineWidth(1)
                
                list_item = QtWidgets.QListWidgetItem()
                
                text = kpl.nama.upper() + " : "
                for n, i in enumerate(kpl.rute_name):
                    if n == len(kpl.rute_name)-1:
                        text += f"{i}"
                    else:
                        text += f"{i} => "
                self.ui.listWidget.addItem(list_item)
                self.ui.listWidget.setItemWidget(list_item, separator)
                self.ui.listWidget.addItem(text)
                self.ui.pushButton_start_simulasi.setEnabled(True)

                self.ui.dateTimeEdit.setDateTime(self.data["Wave"][0]["Tanggal Awal"])
                self.ui.dateTimeEdit_2.setDateTime(self.data["Wave"][0]["Tanggal Awal"])
            
            self.create_pelabuhan()
            self.create_simulation()
            
            del self.train_thread
            self.train_thread = None
   
    def create_simulation(self):
        obj = [ls.Kapal(self.pelabuhan, kpl["nama"], kpl["kategori"], kpl["kapasitas"],kpl["max_voyage"], kpl["rute"], kpl["speed"],kpl) for kpl in self.data["Kapal"]]
        for n,m in enumerate(self.object_kapal):
            rute_name = m.rute_name
            barg = m.full_rute_barang
            obj[n].add_rute(self.pelabuhan, (barg, rute_name))
        self.object_kapal = obj

        # [i.reset(self.pelabuhan) for i in self.object_kapal]
        [i.draw(self.map) for i in self.object_kapal]
        
        wu.add_table_kapal(self.ui.tableWidget_kapal,self.object_kapal)
        wu.add_table_pelabuhan(self.ui.tableWidget_pelabuhan, self.pelabuhan.get_barang())
        
        self.ui.pushButton_Initialize.setEnabled(True)
        self.pushButton_training.setEnabled(False)
        self.ui.pushButton_training.setText("Mulai Training")

    
    def start_simulation(self):
        if self.timer1.isActive():
            self.timer1.stop()
            self.ui.pushButton_start_simulasi.setText('Start Simulasi')
            self.ui.pushButton_reset.setEnabled(True)
        else:
            time_step = 1000*0.1/10
            # self.timer1.start(time_step)
            # self.timer1.start()
            self.timer1.start()
            self.ui.pushButton_start_simulasi.setText('Stop Simulasi')
            self.ui.pushButton_reset.setEnabled(False)
            
    def check_wave(self, max_heigth):
        date = self.ui.dateTimeEdit_2.dateTime()
        awal  = self.data["Wave"][self.wave_count]["Tanggal Awal"]
        akhir = self.data["Wave"][self.wave_count]["Tanggal Akhir"]

        if (date == akhir):
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
            
    def update(self):
        self.check_wave(3)
        if self.date is None:
            self.date = self.ui.dateTimeEdit.dateTime()
            a = self.date.addSecs(0.1*60*60)
            self.ui.dateTimeEdit_2.setDateTime(a)
            self.ui.dateTimeEdit.setEnabled(False)
        else:
            a = self.ui.dateTimeEdit_2.dateTime().addSecs(0.1*60*60)
            self.ui.dateTimeEdit_2.setDateTime(a)
        if self.object_kapal is not None:
            self.n += 1

            # if self.n == 10:
            #     print( self.n, a)

            [i.update(self.pelabuhan) for i in self.object_kapal]
            self.pelabuhan.checking_posisi(self.object_kapal)
            
            cost = sum([float(i.get_data()["Total"]) for i in self.object_kapal])
            

            wu.update_table_kapal(self.ui.tableWidget_kapal,[i.get_data() for i in self.object_kapal])
            wu.update_table_pelabuhan(self.ui.tableWidget_pelabuhan, self.pelabuhan.get_barang())
            wu.update_table_barang(self.ui.tableWidget_2,self.pelabuhan.get_barang_sampai())
            
            # beban_kapal = sum([ float(i.beban_angkut) for i in self.object_kapal])
            # transit = sum([ float(i["Total"]) for i in self.pelabuhan.get_barang_transit()])
            # sisa = sum([ float(i["Total"]) for i in self.pelabuhan.get_barang()])
            # if (beban_kapal <= 0) and (sisa <= 0) and (transit <= 0) and :
            #     if self.timer1.isActive():
            #         self.timer1.stop()
            #         self.ui.pushButton_start_simulasi.setText('Simulasi Selesai')
            #         self.ui.pushButton_start_simulasi.setEnabled(False)
            #         self.ui.pushButton_reset.setEnabled(False)
            
    def reset(self):
        self.map.c
        self.create_pelabuhan()
        self.create_simulation()
        
        self.ui.tableWidget_kapal.clear()
        self.ui.tableWidget_pelabuhan.clear()
        self.ui.tableWidget_2.clear()
        self.pelabuhan.add_barang(self.data["Barang"])
        self.pelabuhan.add_transit(self.data)
        self.ui.dateTimeEdit.setDateTime(self.data["Wave"][0]["Tanggal Awal"])
        self.ui.dateTimeEdit_2.setDateTime(self.data["Wave"][0]["Tanggal Awal"])

        self.layer_cuaca = {}
        self.wave_count = 0
        self.data_wave = []

        self.picker = MplColorHelper("jet", 0,8)
        self.n = 0
        
            
    def file_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.ShowDirsOnly
        self.fileName = QFileDialog.getExistingDirectory(self, options=options)
        if self.fileName:
            # self.path = [join(self.fileName, "Data.xlsx"), join(self.fileName, 'Data Ship.xlsx')]
            # if exists(self.path[0]) and exists(self.path[1]):
            #     self.data = pr.parsing_data_2(self.path)
            #     self.create_pelabuhan()
            file_check = False
            for subdir, dirs, files in os.walk(self.fileName):
                for file in files:
                    filepath = subdir + os.sep + file
                    if filepath.endswith("log cost.csv"):
                        with open(filepath) as csvfile:
                            firstRow = csvfile.readlines(-1)
                            fieldnames = tuple(firstRow[-1].strip('\n').split("\t"))
                            self.cost = float(fieldnames[-1])

                    if filepath.endswith(".pickle"):
                        if (filepath.split("_")[-1]) == "data.pickle" :
                            file = open(filepath, 'rb')
                            self.data = pickle.load(file)
                            file.close()
                            file_check = True
                        elif (filepath.split("_")[-1]) == "ship.pickle":
                            file = open(filepath, 'rb')
                            self.object_kapal = pickle.load(file)
                            file.close()
                            file_check = True
                if file_check:
                    self.create_pelabuhan()

            # else:
            #     reply = QMessageBox.warning(self, 'File Not Found', 'Looking for "Data.xlsx" & "Data Ship.xlsx"',  QMessageBox.Ok)

    def create_pelabuhan(self):
        self.pelabuhan = ls.JaringanPelabuhan()
        [self.ui.comboBox_pelabuhan.addItem(i) for i in sorted([ i for i in self.data['port'] if self.data['port'][i] == "R"])]
        wu.add_table_barang(self.ui.tableWidget_2,self.data["Barang"])
        wu.priview_data(
                    self.ui.pushButton_pilih,
                    self.ui.label_pel_utama,
                    self.ui.label_pel_pengumpul,
                    self.ui.label_pel_pengumpan,
                    self.fileName,
                    self.data["Daftar Pelabuhan"])
        
        self.pelabuhan.add_multiPelabuhan(self.data["Daftar Pelabuhan"])
        # self.pelabuhan.add_rute_from_lis(self.data["Rute"])
        self.pelabuhan.add_extraRoute(self.data["Rute"])
        
        self.pelabuhan.add_barang(self.data["Barang"])
        self.pelabuhan.add_transit_cluster(self.data)
        self.Total_Nilai_Harga, self.data["Barang"] = self.pelabuhan.add_Harga(self.data["Harga Barang"], self.data["Daftar Pelabuhan"], self.data["Barang"])
        self.pelabuhan.draw(self.map, False, self.data["Spesial PR"], self.picker)
        
        wu.add_table(self.ui.tableWidget,self.data["Barang"])
        self.label_total_cost.setText("{:,.2f}".format(self.cost))
        self.label_total_Revenue.setText("{:,.2f}".format(self.Total_Nilai_Harga - self.cost))
        self.create_simulation()

        self.ui.dateTimeEdit.setDateTime(self.data["Wave"][0]["Tanggal Awal"])
        self.ui.dateTimeEdit_2.setDateTime(self.data["Wave"][0]["Tanggal Awal"])

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
    
    def save(self):
        if self.data is not None or True:
            self.ui.pushButton_Initialize.setEnabled(True)
            
    def download(self):
        pass
            
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Quit', 'Are You Sure to Quit?', QMessageBox.No | QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            if self.train_thread is not None:
                self.train_thread.stop()
                self.ui.pushButton_training.setText("Mulai Training")
                del self.train_thread
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    Dialog = Main()
    Dialog.setWindowTitle("")
    Dialog.showMaximized()
    sys.exit(app.exec_())

