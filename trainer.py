from training import train
popSize = 5
elitsize = 3
mutation = 0.5
generation = 2

path = ["data/Data.xlsx", "data/Data Ship.xlsx"]

trainer = train.GA_Trainer(path[0], path[1],popSize,elitsize,mutation)
trainer.initialPopulation(popSize)

for i in range(generation):
    cost = trainer.nextGeneration()
trainer.check_best_result()
trainer.save()