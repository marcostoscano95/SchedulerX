import json
import numpy

from datetime import datetime, timedelta
from deap import creator, base, tools, algorithms
from pprint import pprint

# Dict with student_id: [list of tests ids]
with open('data/enrolled.json') as f:
    enrolled_by_subject = json.load(f)

tests = {}
students_by_subjectid = {}
for i, subject_name in enumerate(enrolled_by_subject):
    students_by_subjectid[i] = enrolled_by_subject[subject_name]
    tests[i] = subject_name

students = {}
num_student_by_subject_id = {}
for subject_id in students_by_subjectid:
    for enrolled_student in students_by_subjectid[subject_id]:
        students.setdefault(enrolled_student, set()).add(subject_id)
    num_student_by_subject_id[subject_id] = len(students_by_subjectid[subject_id])

students_with_at_least_to_test = {}

for student in students:
    if len(students[student]) > 1:
        students_with_at_least_to_test[student] = students[student]

num_tests = len(tests)
num_students_with_at_least_to_test = len(students_with_at_least_to_test)

num_days = 8
day = datetime.now().replace(day=1, minute=0)
timeslots = []
for slot in range(num_days):
    timeslots.append(day.replace(hour=9))
    timeslots.append(day.replace(hour=14))
    timeslots.append(day.replace(hour=18))
    day = day + timedelta(days=1)

max_time_distance = (timeslots[-1] - timeslots[0]).total_seconds()
num_timeslots = len(timeslots)


# The toolbox stored the setup of the algorithm.
# It describes the different elements to take into account.
toolbox = base.Toolbox()

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", numpy.ndarray, fitness=creator.FitnessMax)

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
    return min(
        [tests_distance(test_a, test_b, calendar)
         for (test_a, test_b) in zip(student_test_ordered, student_test_ordered[1:])]
    )


def avg_students_min_tests_distance(calendar):
    """Returns the average of the minimum time distance in seconds
    between tests in the calendar"""
    return sum(
        [student_min_tests_distance(calendar, students_with_at_least_to_test[student])
         for student in students_with_at_least_to_test]
    ) / num_students_with_at_least_to_test


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


def capacity_exceed(test_dates):
    return [sum([num_student_by_subject_id[test_id] for test_id in test_dates[test_date]])
            for test_date in test_dates]


def total_capacity_exceed(calendar):
    test_dates = {}
    for test_id in calendar:
        test_dates.setdefault(calendar[test_id], set()).add(test_id)

    return max(capacity_exceed(test_dates))


def bad_luck_students(calendar):
    return len(
        [student_min_tests_distance(calendar, students_with_at_least_to_test[student])
         for student in students_with_at_least_to_test
         if student_min_tests_distance(calendar, students_with_at_least_to_test[student]) == 0]
    )


def evaluation(individual):
    """Evaluation function for a individual"""
    calendar = decode_calendar(individual)
    fitness = 4 * avg_students_min_tests_distance(calendar) / max_time_distance
    fitness -= 8 * bad_luck_students(calendar) / num_students_with_at_least_to_test
    fitness -= 0.5 * total_capacity_exceed(calendar) / 4000
    return (fitness, )


toolbox.register("evaluate", evaluation)

# We will employ tournament selection with size 3
toolbox.register("select", tools.selTournament, tournsize=3)

# Population of 100 individuals.
pop = toolbox.population(n=100)

first_stats = tools.Statistics(key=lambda ind: ind.fitness.values[0])
stats = tools.MultiStatistics(obj1=first_stats)
stats.register("min", numpy.max, axis=0)

# crossover_probabilty=0.8; mutate_probabilty=0.2; 400 generations
result, log = algorithms.eaSimple(
    pop, toolbox, cxpb=0.8, mutpb=0.2, ngen=1000, stats=stats, verbose=True)

# Get best individual
best_individual = tools.selBest(result, k=1)[0]
calendar = decode_calendar(best_individual)

print('avg_students_min_tests_distance: {} hours'.format(
    avg_students_min_tests_distance(calendar) / 3600)
)
print('Bad luck students: {}'.format(bad_luck_students(calendar)))
print('Max #students in a timescope: {}'.format(total_capacity_exceed(calendar)))

result = {}

for test, date in calendar.items():
    result.setdefault(date.strftime('%d/%m %HH:%MM'), {}
                      ).setdefault('testnames', []).append(tests[test])
    result[date.strftime('%d/%m %HH:%MM')].setdefault('count', 0)
    result[date.strftime('%d/%m %HH:%MM')]['count'] += num_student_by_subject_id[test]

pprint(result)
