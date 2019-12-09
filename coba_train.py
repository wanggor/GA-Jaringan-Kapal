from training import train

data = {}
data["path"] = ["data/Data.xlsx", "data/Data Ship.xlsx"]
data['popSize'],data['eliteSize'],data['Mutation Rate'] = 3, 1, 0.007

trainer = train.GA_Trainer(data["path"][0], data["path"][1],3,2,0.1)

trainer.initialPopulation(3)

for i in range(3):
    cost = trainer.nextGeneration()
    print("************")
    print(cost)
    print("************")

print("####################")
trainer.check_best_result()