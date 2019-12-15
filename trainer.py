from training import train

with open("parameter training.txt") as f:
    data =  [float(i.strip().split("=")[-1].strip()) for i in f.readlines()]

path = ["data/Data.xlsx", "data/Data Ship.xlsx"]

trainer = train.GA_Trainer(path[0], path[1],int(data[0]),int(data[1]),data[2])
trainer.initialPopulation(int(data[0]))

for i in range(int(data[3])):
    cost = trainer.nextGeneration()
trainer.check_best_result()
trainer.save()