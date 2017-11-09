import numpy
from deap import creator, base, tools, algorithms

tests = [[1, 2, 3, 4], [1, 3, 4, 5], [1, 2, 4],  [1, 2, 4],
         [1, 2, 4],  [1, 2, 4],  [1, 2, 4],  [1, 2, 4]]

time_slots = [3, 3, 3, 3, 3, 2]

toolbox = base.Toolbox()

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox.register("indices", numpy.random.permutation, len(tests) + sum(time_slots))
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.indices)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

toolbox.register("mate", tools.cxOrdered)
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)


def evaluation(individual):
    pass


toolbox.register("evaluate", evaluation)

toolbox.register("select", tools.selTournament, tournsize=3)

pop = toolbox.population(n=100)

result, log = algorithms.eaSimple(pop, toolbox, cxpb=0.8, mutpb=0.2, ngen=400, verbose=False)

best_individual = tools.selBest(result, k=1)[0]
print('Fitness of the best individual: ', evaluation(best_individual)[0])
