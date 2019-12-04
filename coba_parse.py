from utils import preprocessing
from training import trainer


path = ["data/Data.xlsx", "data/Data Ship.xlsx"]
# data = preprocessing.parsing_data_2(path)

# print(data["Spesial PR"])

T = trainer.GA_Trainer(path[0], path[1], 2, 1, 0.01)
T.initialPopulation(2)
for i in T.pupulation_kapal[0]:
    if i.kategori == "PR":
        pass
        # print(i.nama, len(i.rute_name), i.rute_name)