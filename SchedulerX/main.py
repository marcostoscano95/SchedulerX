# import random
import numpy
from deap import creator, base, tools, algorithms
from datetime import datetime, timedelta

students = {
    1: [0, 1],
    2: [0, 3],
    3: [0, 3],
    4: [1, 2],
    5: [1, 3],
    6: [2, 3],
    7: [0, 1],
    8: [0, 2],
    9: [0, 3],
    10: [1, 2],
    11: [1, 3],
    12: [2, 3],
    13: [0, 1],
    14: [1, 2],
    15: [1, 3],
    16: [1, 2],
    17: [1, 3],
    18: [1, 2],
    19: [1, 2],
    20: [1, 2],
}

tests = [0, 1, 2, 3]

related = [[0, 1], [2, 3]]

# related = {
#     'calculo1': []
#     'gal1': []
#     'calculo2':
#     'gal2':
#     'matd1':
#     'programacion1':
# }

today = datetime.now()
time_slots = [today, today + timedelta(days=1)]

toolbox = base.Toolbox()

creator.create("FitnessMin", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox.register("indices", numpy.random.permutation, len(tests) + len(time_slots))
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.indices)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)

toolbox.register("mate", tools.cxOrdered)
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)


def tests_distance(a, b, calendar):
    return (calendar[b] - calendar[a]).total_seconds()


def student_min_tests_distance(calendar, student_tests):
    student_test_ordered = sorted(student_tests, key=lambda x: calendar[x])
    return (
        min([tests_distance(a, b, calendar)
             for (a, b) in zip(student_test_ordered, student_test_ordered[1:])]
            )
    )


def avg_students_min_tests_distance(calendar):
    return (sum([student_min_tests_distance(calendar, student_tests)
                 for student_tests in students.values()]) / len(students))


def decode_calendar(individual):
    calendar = {}
    tmp = []
    slots = []
    for i in individual:
        if i < len(tests):
            tmp.append(i)
        else:
            slots.append(i)
            for test in tmp:
                calendar[test] = time_slots[i - len(tests)]
            tmp = []

    for test in tmp:
        calendar[test] = time_slots[slots[0] - len(tests)]

    return calendar


def evaluation(individual):
    calendar = decode_calendar(individual)
    return (avg_students_min_tests_distance(calendar),)


toolbox.register("evaluate", evaluation)

toolbox.register("select", tools.selTournament, tournsize=3)

pop = toolbox.population(n=100)

result, log = algorithms.eaSimple(pop, toolbox, cxpb=0.8, mutpb=0.2, ngen=400, verbose=False)

best_individual = tools.selBest(result, k=1)[0]

print('Fitness of the best individual: ', evaluation(best_individual)[0] / 3600)
print('Test | Date')
for test, date in decode_calendar(best_individual).items():
    print('  {}   {}'.format(test, date.strftime(' %d %HH:%MM')))
