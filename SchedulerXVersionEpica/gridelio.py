import json
import numpy
import itertools
import operator

from datetime import datetime, timedelta
from deap import creator, base, tools, algorithms
from pprint import pprint
from custom_map import custom_map

# generar pdf
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import A4, cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER,TA_RIGHT
from reportlab.lib import colors

# Dict with student_id: [list of tests ids]
with open('data/enrolled.json') as f:
    enrolled_by_subject = json.load(f)

with open('data/salones.json') as p:
    enrolled_by_salones = json.load(p)

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
num_student_by_subject = sum(num_student_by_subject_id.values())

for student in students:
    if len(students[student]) > 1:
        students_with_at_least_to_test[student] = students[student]

num_tests = len(tests)
num_students_with_at_least_to_test = len(students_with_at_least_to_test)

num_days = 9
day = datetime.now().replace(day=1, minute=0)
daypdf = datetime.now().replace(day=1, minute=0)
dataDias = []
timeslots = []
for slot in range(num_days):
    dataDias.append(day.date().strftime("%A") + " " + str(day.date().day) +"/"+ str(day.date().month))
    timeslots.append(day.replace(hour=9))
    timeslots.append(day.replace(hour=14))
    timeslots.append(day.replace(hour=18))
    if day.date().strftime("%A") == "Saturday":
        day = day + timedelta(days=2)
    else:
        day = day + timedelta(days=1)

max_time_distance = (timeslots[-1] - timeslots[0]).total_seconds()
num_timeslots = len(timeslots)

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

#def test_whit_timeslots(calendar):


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
    avg = avg_students_min_tests_distance(calendar)
    bad = bad_luck_students(calendar)
    capa = total_capacity_exceed(calendar)
    fitness1 = 2 * (avg / max_time_distance) ** 2
    fitness2 = 4 * (1 - bad / num_students_with_at_least_to_test) ** 2
    fitness3 = (capa / num_student_by_subject) ** 2
    return (fitness1 + fitness2 - fitness3,)

order_num_students_by_subject_id = sorted(num_student_by_subject_id.items(), key=operator.itemgetter(1))
order_num_students_by_subject_id.reverse()

best_individual = []

for idx in range(0,num_tests + num_timeslots - 1):
    best_individual.append(idx)

cant_pos = num_timeslots - 1
best_fittnes = (-30,)
position_fittnes = 0
position = 0

for idx_test,num_student_test in order_num_students_by_subject_id:
    best_individual.remove(idx_test)
    best_fittnes = (-30,)
    position =  0
    for index in range(0,num_tests + num_timeslots - 2):
        best_individual.insert(index,idx_test)
        position_fittnes = evaluation(best_individual)
        if best_fittnes[0] < position_fittnes[0]:
            best_fittnes = position_fittnes
            position = index
        best_individual.pop(index)
    best_individual.insert(position,idx_test)

calendar = decode_calendar(best_individual)
result = {}

for test, date in calendar.items():
    result.setdefault(date.strftime('%d/%m %HH:%MM'), {}
                      ).setdefault('testnames', []).append(tests[test])
    result[date.strftime('%d/%m %HH:%MM')].setdefault('count', [])
    result[date.strftime('%d/%m %HH:%MM')]['count'].append(num_student_by_subject_id[test])
    result[date.strftime('%d/%m %HH:%MM')].setdefault('salones',[])

# stats1 = best_fittnes[0]
# stats1.register("max", numpy.max)
# stats1.register("avg", numpy.mean)
# stats1.register("min", numpy.min)
# stats1.register("std", numpy.std)
#
# print(stats1)

for i, date_time in enumerate(result):
    ola = result[date_time]['count']
    salones = []
    for i, sal in enumerate(enrolled_by_salones):
        salones.append(sal)
    for nodo in range(0,len(ola)):
        salones_por_materia = []
        itertools.permutations(salones, len(salones))
        aux = ola[nodo]
        for salon in salones:
            if aux - enrolled_by_salones[salon][0] <= 0 and aux - enrolled_by_salones[salon][0] > -20:
                salones_por_materia.append(salon)
                salones.remove(salon)
                break
            else:
                if aux - enrolled_by_salones[salon][0]  > 0:
                    aux -= enrolled_by_salones[salon][0]
                    salones_por_materia.append(salon)
                    salones.remove(salon)
        result[date_time]['salones'].append(salones_por_materia)

# Create PDF XD
width, height = A4

def coord(x, y, unit=1):
    x, y = x * unit, height -  y * unit
    return x, y

# Styles
styles = getSampleStyleSheet()
styleN = styles["BodyText"]
styleN.alignment = TA_LEFT
styleBH = styles["Normal"]
styleBH.alignment = TA_CENTER

# Headers
hdescrpcion = Paragraph('''<b>Calendario de Parciales/Examenes</b>''', styleBH)

# Texts
#descrpcion = Paragraph('long paragraph', styleN)

fila = 2
story = []
data=   [['',hdescrpcion,''],
        ['','', '']]
styletable =    [('BOX',(0,0),(-1,0),2,colors.black),
                ('BOX',(0,1),(-1,1),2,colors.black),
                ('BOX',(0,0),(-1,-1),2,colors.black),
                ('BACKGROUND',(0,0),(3,0),colors.pink)]

for slots in range(num_days):
    data.append(['',"Dia "+str(slots+1) + " - " + dataDias[slots],''])
    styletable.append(('BOX',(0,int(fila)),(-1,int(fila)),2,colors.black))
    styletable.append(('BACKGROUND',(0,int(fila)),(3,int(fila)),colors.yellow))
    styletable.append(('ALIGN',(1,int(fila)),(1,int(fila)),'CENTER'))
    fila = fila + 1
    if daypdf.replace(hour=9).strftime('%d/%m %HH:%MM') in result:
        data.append(['',"Hora "+daypdf.replace(hour=9).strftime('%H:%M'),''])
        styletable.append(('BOX',(0,int(fila)),(-1,int(fila)),1,colors.black))
        styletable.append(('BACKGROUND',(0,int(fila)),(3,int(fila)),colors.grey))
        styletable.append(('ALIGN',(1,int(fila)),(1,int(fila)),'CENTER'))
        ola = result[daypdf.replace(hour=9).strftime('%d/%m %HH:%MM')]['testnames']
        for nodo in range(0,len(ola)):
            data.append(["# "+ola[nodo],'',''])
            str1 = ' - '.join(str(e) for e in result[daypdf.replace(hour=9).strftime('%d/%m %HH:%MM')]['salones'][nodo])
            data.append(['','',Paragraph('Salones: ' + str1,styleN)])
            fila = fila + 2
        fila = fila + 1

    if daypdf.replace(hour=14).strftime('%d/%m %HH:%MM') in result:
        data.append(['',"Hora "+daypdf.replace(hour=14).strftime('%H:%M'),''])
        styletable.append(('BOX',(0,int(fila)),(-1,int(fila)),1,colors.black))
        styletable.append(('BACKGROUND',(0,int(fila)),(3,int(fila)),colors.grey))
        styletable.append(('ALIGN',(1,int(fila)),(1,int(fila)),'CENTER'))
        ola = result[daypdf.replace(hour=14).strftime('%d/%m %HH:%MM')]['testnames']
        for nodo in range(0,len(ola)):
            data.append(["# "+ola[nodo],'',''])
            str1 = ' - '.join(str(e) for e in result[daypdf.replace(hour=14).strftime('%d/%m %HH:%MM')]['salones'][nodo])
            data.append(['','',Paragraph('Salones:  ' + str1,styleN)])
            fila = fila + 2
        fila = fila + 1

    if daypdf.replace(hour=18).strftime('%d/%m %HH:%MM') in result:
        data.append(['',"Hora "+daypdf.replace(hour=18).strftime('%H:%M'),''])
        styletable.append(('BOX',(0,int(fila)),(-1,int(fila)),1,colors.black))
        styletable.append(('BACKGROUND',(0,int(fila)),(3,int(fila)),colors.grey))
        styletable.append(('ALIGN',(1,int(fila)),(1,int(fila)),'CENTER'))
        ola = result[daypdf.replace(hour=18).strftime('%d/%m %HH:%MM')]['testnames']
        for nodo in range(0,len(ola)):
            data.append(["# "+ola[nodo],'',''])
            str1 = ' - '.join(str(e) for e in result[daypdf.replace(hour=18).strftime('%d/%m %HH:%MM')]['salones'][nodo])
            data.append(['','',Paragraph('Salones:  ' + str1,styleN)])
            fila = fila + 2
        fila = fila + 1

    if daypdf.date().strftime("%A") == "Saturday":
        daypdf = daypdf + timedelta(days=2)
    else:
        daypdf = daypdf + timedelta(days=1)

t = Table(data, colWidths=[6 * cm, 6 * cm, 6 * cm])

t.setStyle(TableStyle(styletable))
#                     ('GRID',(1,1),(-2,-2),1,colors.green),
#                     ('BOX',(0,0),(1,-1),2,colors.red),
#                     ('LINEABOVE',(1,2),(-2,2),1,colors.blue),
#                     ('LINEBEFORE',(2,1),(2,-2),1,colors.pink),
#                     ('BACKGROUND', (0, 0), (0, 1), colors.pink),
#                     ('BACKGROUND', (1, 1), (1, 2), colors.lavender),
#                     ('BACKGROUND', (2, 2), (2, 3), colors.orange),
#                     ('BOX',(0,0),(-1,-1),2,colors.black),
#                     ('GRID',(0,0),(-1,-1),0.5,colors.black),
#                     ('VALIGN',(3,0),(3,0),'BOTTOM'),
#                     ('BACKGROUND',(3,0),(3,0),colors.limegreen),
#                     ('BACKGROUND',(3,1),(3,1),colors.khaki),
#                     ('ALIGN',(3,1),(3,1),'CENTER'),
#                     ('BACKGROUND',(3,2),(3,2),colors.beige),
#                     ('ALIGN',(3,2),(3,2),'LEFT'),
story.append(t)
doc = SimpleDocTemplate(
        "GreedyNeoLiberal.pdf",
        pagesize=A4,
showBoundary=0)
doc.build(story)

pprint(result)
