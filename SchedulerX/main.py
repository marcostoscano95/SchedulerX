import json
import numpy

from datetime import datetime, timedelta
from deap import creator, base, tools, algorithms

# Dict with student_id: [list of tests ids]
with open('data/enrolled.json') as f:
    enrolled_by_subject = json.load(f)

tests = {}
enrolled_by_subjectid = {}
for i, subject_name in enumerate(enrolled_by_subject):
    enrolled_by_subjectid[i] = enrolled_by_subject[subject_name]
    tests[i] = subject_name

students2 = {}
for subject_id in enrolled_by_subjectid:
    for enrolled_student in enrolled_by_subjectid[subject_id]:
        students2.setdefault(enrolled_student, set()).add(subject_id)

students = {}
for student in students2:
    if len(students2[student]) > 1:
        students[student] = students2[student]

today = datetime.now()
timeslots = [today, today + timedelta(days=1)]
num_timeslots = len(timeslots)

# The toolbox stored the setup of the algorithm.
# It describes the different elements to take into account.
toolbox = base.Toolbox()

creator.create("FitnessMin", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox.register("indices", numpy.random.permutation, num_tests + num_timeslots)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.indices)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


# Ordered crossover (OX).
toolbox.register("mate", tools.cxOrdered)

# Mutation that swap elements from two points of the individual.
toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)


def tests_distance(test_a, test_b, calendar):
    """Return the time distance in seconds between two tests in the calendar"""
    return (calendar[test_b] - calendar[test_a]).total_seconds()


def student_min_tests_distance(calendar, student_tests):
    """Return the minimum time distance in seconds
    between any two tests of a student in the calendar"""
    student_test_ordered = sorted(student_tests, key=lambda x: calendar[x])
    return (
        min([tests_distance(test_a, test_b, calendar)
             for (test_a, test_b) in zip(student_test_ordered, student_test_ordered[1:])]
            )
    )


def avg_students_min_tests_distance(calendar):
    """Returns the average of the minimum time distance in seconds
    between tests in the calendar"""
    return (sum([student_min_tests_distance(calendar, student_tests)
                 for student_tests in students.values()]) / len(students))


def is_test(idx):
    """Return True if the index of an individual is a test otherwise return False"""
    return idx < num_tests


def decode_calendar(individual):
    """Returns a calendar of tests in a dict like <test_id>:<datetime>"""
    calendar = {}
    tests_without_timeslot = []
    seen_slots = []
    for idx in individual:
        if is_test(idx):
            tests_without_timeslot.append(idx)
        else:  # is a time_slot
            seen_slots.append(idx)
            for test in tests_without_timeslot:
                calendar[test] = timeslots[idx - num_tests]
            tests_without_timeslot = []

    # The individual is a circular array, if there are tests left,
    # we assing them to the first timeslot
    for test in tests_without_timeslot:
        calendar[test] = timeslots[seen_slots[0] - num_tests]

    return calendar


def evaluation(individual):
    """Evaluation function for a individual"""
    calendar = decode_calendar(individual)
    return (avg_students_min_tests_distance(calendar),)


toolbox.register("evaluate", evaluation)

# We will employ tournament selection with size 3
toolbox.register("select", tools.selTournament, tournsize=3)

# Population of 100 individuals.
pop = toolbox.population(n=100)

# crossover_probabilty=0.8; mutate_probabilty=0.2; 400 generations
result, log = algorithms.eaSimple(pop, toolbox, cxpb=0.8, mutpb=0.2, ngen=400, verbose=False)

# Get best individual
best_individual = tools.selBest(result, k=1)[0]

print('Fitness of the best individual: ', evaluation(best_individual)[0] / 3600)
print('Test | Date')
for test, date in decode_calendar(best_individual).items():
    print('  {}   {}'.format(test, date.strftime(' %d %HH:%MM')))
