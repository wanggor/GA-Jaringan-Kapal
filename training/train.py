# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 14:07:57 2019

@author: wanggor
"""

from PyQt5.QtCore import QThread, pyqtSignal
import numpy as np
import time

import pandas as pd
import utils.training_utils as tu
from training.trainer import GA_Trainer
import time

class Train(QThread):
    data = pyqtSignal(dict)
    def __init__(self, parameter,parent=None):
        super(Train, self).__init__(parent)
        self.kill = False
        self.trainer = GA_Trainer(parameter['path'][0],parameter['path'][1], 
                                  parameter['popSize'], 
                                  parameter['eliteSize'], 
                                  parameter['Mutation Rate'])
        
        
        self.generation = parameter['Generations']
        self.popSize = parameter['popSize']
        
    def run(self):
        i=0
        remaining_history = []
        self.trainer.initialPopulation(self.popSize)
        while (not self.kill) and (self.generation > i) :
            i +=1
            cost = self.trainer.nextGeneration()
            remaining_history.append(cost)
            data = {}
            data["y"] = remaining_history
            data["msg"] = f"{i} |  cost : {cost}"
            self.data.emit(data)
        self.send_kapal()
        self.save()
        
    def send_kapal(self):
        data  = {}
        best_route = self.trainer.extract_best_route()
        data["Kapal"] = best_route
        self.data.emit(data)
    
    def save(self):
        self.trainer.save()
            
    def stop(self):
        self.kill = True
        self.wait()
            
            
                
    
    