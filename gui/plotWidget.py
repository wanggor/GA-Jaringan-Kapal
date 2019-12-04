# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 07:37:36 2019

@author: wanggor
"""
import pyqtgraph as pg
from PyQt5.QtCore import Qt

class LineGraph():
    def __init__(self,title):
        self.title = title
        self.widget = pg.PlotWidget(
                    title=f"<h4>{title.upper()}<\h4>", 
                    labels = {'bottom': "Jumlah Iterasi","top":"Sisa Barang"},
                    titlePen = 'k')
        
        self.widget.setMaximumHeight(300)
        self.widget.enableAutoRange(True)
        self.widget.setBackground((0,0,0,0))
        self.widget.getAxis('bottom').setPen('k')
        self.widget.getAxis('left').setPen('k')
        self.widget.setStyleSheet("background-color:white")
        
        self.pen = pg.mkPen((26, 187, 156), width=3, style=Qt.SolidLine) 
        self.penSymbol = pg.mkPen((26, 187, 156), width=3, style=Qt.SolidLine) 
        
    def update(self, data):
        self.widget.clear()
        y = data["y"]
        
        self.widget.setTitle("<h4>{}<\h4>".format(self.title.upper()))
        self.widget.plot(y,fillLevel=-0.3, brush=(26, 187, 156,100),pen = self.pen,symbolBrush='w', symbolPen=self.penSymbol,symbolSize=1)
        