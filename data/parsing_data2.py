# -*- coding: utf-8 -*-

import pandas as pd
from training_utils import parse_dms


data =pd.read_excel("Data.xlsx", sheet_name="TL_char", index_col = "Unnamed: 0").to_dict()

print(data["ship_char"])

#exel = pd.ExcelFile("Data Ship.xlsx")
#
#data = {}
#
#for name in exel.sheet_names:
#    ex = exel.parse(sheet_name=name)
#    data[name] = {}
#    data[name]["type"] = ex.iloc[0,1]
#    data[name]["pelabuhan asal"] = ex.iloc[0,2]
#    data[name]["route"] = list(ex.iloc[:,3].values)
#    
#print(data["TL2"])
