# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 09:29:50 2019

@author: wanggor
"""

from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from re import split


def add_table(table_obj,data):
    count_row = len(data)
    column_index = list(data[0].keys())
    count_columns = len(column_index)
    
    table_obj.setRowCount(count_row)
    table_obj.setColumnCount(count_columns)
    
    table_obj.setHorizontalHeaderLabels(column_index)
    table_obj.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
    for n,row in enumerate(data):
        for j,key in enumerate(data[n]):
              if key == "Nilai Barang":
                    item = QTableWidgetItem("{:,.2f}".format(data[n][key]))
                    table_obj.setItem(n,j,item)
                    item.setTextAlignment(Qt.AlignRight)
              else:
                    table_obj.setItem(n,j, QTableWidgetItem(str(data[n][key])))
            
def add_table_barang(table_obj,data):
    count_row = len(data)
    table_obj.setRowCount(count_row)
    table_obj.setColumnCount(4)
    # table_obj.setHorizontalHeaderLabels(["Kode Barang", "Pelabuhan Asal", "Pelabuhan Tujuan", "Penyelesaian", "Pendapatan"])
    table_obj.setHorizontalHeaderLabels(["Kode Barang", "Pelabuhan Asal", "Pelabuhan Tujuan", "Penyelesaian"])
    table_obj.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

#TODO 
def update_table_barang(table_obj,data):
    data = sorted(data, key=lambda k: float([i for i in split(r'(\d+)',k['Kode Barang']) if i][1])) 
    for n,item in enumerate(data):
        if item["Total"] != 0:
            
            percentage = str(int(100*item["Bobot"]/item["Total"]))+" %"
        else:
            percentage = "-"
        table_obj.setItem(n,0, QTableWidgetItem(str(item["Kode Barang"])))
        table_obj.setItem(n,1, QTableWidgetItem(item["Asal Pelabuhan"]))
        table_obj.setItem(n,2, QTableWidgetItem(item["Tujuan Pelabuhan"]))
        table_obj.setItem(n,3, QTableWidgetItem(str(item["Bobot"]) + f' ({percentage})'))
        # biaya = float(item["Biaya"]) * item["Bobot"]/item["Total"]
        # item = QTableWidgetItem("{:,.2f}".format(biaya))
        # table_obj.setItem(n,4,item)
        # item.setTextAlignment(Qt.AlignRight)
    
            
def add_table_kapal(table_obj, data):
    count_row = len(data)
    
    table_obj.setRowCount(count_row)
    table_obj.setColumnCount(4)
    
    # table_obj.setHorizontalHeaderLabels(["Nama", "Kapasitas", "Lama Perjalanan", "Posisi", "Cost"])
    table_obj.setHorizontalHeaderLabels(["Nama", "Kapasitas", "Lama Perjalanan", "Posisi"])
    table_obj.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
def update_table_kapal(table_obj,data):
    data = sorted(data, key=lambda k: k['Nama']) 
    for n,item in enumerate(data):
        table_obj.setItem(n,0, QTableWidgetItem(item["Nama"] + f" ({item['Kategori']})"))
        table_obj.setItem(n,1, QTableWidgetItem(item["Kapasitas"]))
        table_obj.setItem(n,2, QTableWidgetItem(item["Lama Perjalanan"]))
        table_obj.setItem(n,3, QTableWidgetItem(item["Lokasi"]))
        # item = QTableWidgetItem("{:,.2f}".format(float(item["Total"])))
        # table_obj.setItem(n,4,item)
        # item.setTextAlignment(Qt.AlignRight)


def add_table_pelabuhan(table_obj, data):
    count_row = len(data)
    
    table_obj.setRowCount(count_row)
    table_obj.setColumnCount(4)
    
    table_obj.setHorizontalHeaderLabels(["Pelabuhan", "Berat Barang", "Transit", "Kondisi", "Jumlah Nominal"])
    table_obj.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

  
def update_table_pelabuhan(table_obj,data):
    data = sorted(data, key=lambda k: k['Total'], reverse = True) 
    for n,item in enumerate(data):
        table_obj.setItem(n,0, QTableWidgetItem(item["Pelabuhan"]))
        table_obj.setItem(n,1, QTableWidgetItem(str(item["Total"])))
        table_obj.setItem(n,2, QTableWidgetItem(str(item["Transit"])))
        table_obj.setItem(n,3, QTableWidgetItem(str(item["Kondisi"])))
        item = QTableWidgetItem("{:,.2f}".format(float(item["Total Nominal"])))
        table_obj.setItem(n,4,item)
        item.setTextAlignment(Qt.AlignRight)
        
def priview_data(pushButton_pilih, label_pel_utama, label_pel_pengumpul,label_pel_pengumpan, file_name, data):
    pushButton_pilih.setText(file_name.split("/")[-1].split("\\")[-1])
    
    label_pel_utama.setText(" : " + str(len([i for i in data if i["Tipe"].lower() == 'u'])))
    label_pel_pengumpul.setText(" : " + str(len([i for i in data if i["Tipe"].lower() == 'p'])))
    label_pel_pengumpan.setText(" : " + str(len([i for i in data if i["Tipe"].lower() == 'r'])))
    