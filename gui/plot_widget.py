from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
import math
import os


from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import cm

class PlotWidget():

    def __init__(self, *args, **kwargs):
        # super().__init__(*args, **kwargs)

        self.widget = QtWidgets.QLabel()

        fig = plt.figure()
        fig.subplots_adjust(left=0.08,right=0.99,
                            bottom=0.1,top=0.9,
                            hspace=0,wspace=0)
        plt.tight_layout()
        fig.patch.set_facecolor("None")

        layout = QtWidgets.QVBoxLayout(self.widget)

        self.canvas = FigureCanvas(fig)
        self.canvas.figure.subplots().patch.set_alpha(0)
        self.canvas.setStyleSheet("background-color:transparent;")

        layout.addWidget(self.canvas)

        # layout.addWidget(self.canvas)

        # self.setLayout(layout)

    def update(self,data= [[0,1,2,3],[0,2,4,6]]):
        ax = self.canvas.figure.subplots()
        ax.clear()

        ax.plot(data[0],data[1])
        ax.fill_between(data[0],data[1],0, alpha=0.3, color='b')

        ax.set_ylabel('Waktu (menit)')
        ax.set_ylim([0,data[1][-1]+1])
        ax.set_xlim([0,data[0][-1]+1])
        ax.set_title('Jumlah Kendaraan')
        ax.margins(x=0, y=0)
        ax.patch.set_alpha(0)
        self.canvas.setStyleSheet("background-color:transparent;")
        ax.figure.canvas.draw()
        # self.update()