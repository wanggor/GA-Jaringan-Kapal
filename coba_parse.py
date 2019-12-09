from utils import preprocessing
from training import trainer
from models import logistic_models as ls


# path = ["data/Data.xlsx", "data/Data Ship.xlsx"]
# data = preprocessing.parsing_data_2(path)

# pelabuhan = ls.JaringanPelabuhan()
# pelabuhan.add_multiPelabuhan(data["Daftar Pelabuhan"])
# pelabuhan.add_rute_from_lis(data["Rute"])
# pelabuhan.add_barang(data["Barang"])
# pelabuhan.add_transit_cluster(data)

# print([i[1].barang for i in pelabuhan.lis_pelabuhan.items()])