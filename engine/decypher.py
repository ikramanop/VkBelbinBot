import json
import operator
import os
from math import pi, ceil

import matplotlib.pyplot as plt
import openpyxl
import pandas as pd

from database.connector import DbConnector

pattern = {
    "Д":      {1: 7, 2: 9, 3: 24, 4: 28, 5: 34, 6: 46, 7: 53},
    "П":      {1: 4, 2: 10, 3: 17, 4: 32, 5: 38, 6: 43, 7: 55},
    "В.С.":   {1: 6, 2: 13, 3: 19, 4: 26, 5: 36, 6: 47, 7: 49},
    "М":      {1: 3, 2: 15, 3: 20, 4: 29, 5: 40, 6: 41, 7: 54},
    "И.Р.":   {1: 1, 2: 11, 3: 22, 4: 31, 5: 37, 6: 48, 7: 52},
    "О":      {1: 8, 2: 12, 3: 23, 4: 27, 5: 33, 6: 45, 7: 50},
    "К":      {1: 2, 2: 14, 3: 21, 4: 25, 5: 35, 6: 42, 7: 56},
    "Д.д.К.": {1: 5, 2: 16, 3: 18, 4: 30, 5: 39, 6: 44, 7: 51}
}

name_map = {
    "Д":      "Действующий",
    "П":      "Председатель",
    "В.С.":   "Возмутитель спокойствия",
    "М":      "Мыслитель",
    "И.Р.":   "Исследователь ресурсов",
    "О":      "Оценивающий",
    "К":      "Коллективист",
    "Д.д.К.": "Доводящий до конца"
}


def form_result_string(text):
    result = []
    for rec in text.split(';')[:-1]:
        result.append(rec.split(': ')[1])

    return result


def write_result(result_dict, peer_id, db: DbConnector):
    result_string = ''
    for alias, sum in result_dict.items():
        result_string += name_map[alias] + ": " + str(round(sum / 70 * 100)) + '%;'
    db.update_result(peer_id, result_string,
                     name_map[max(result_dict.items(), key=operator.itemgetter(1))[0]])


def write_excel(peer_id, db: DbConnector):
    if not os.path.exists('result/result.xlsx'):
        if not os.path.exists('result'):
            os.mkdir('result')
        wb = openpyxl.Workbook()
        sheet = wb.active
        sheet.title = 'Результаты тестирования'
        sheet['A1'] = 'Имя'
        sheet['B1'] = 'Имя из вк'
        sheet['C1'] = 'Действующий'
        sheet['D1'] = 'Председатель'
        sheet['E1'] = 'Возмутитель спокойствия'
        sheet['F1'] = 'Мыслитель'
        sheet['G1'] = 'Исследователь ресурсов'
        sheet['H1'] = 'Оценивающий'
        sheet['I1'] = 'Коллективист'
        sheet['J1'] = 'Доводящий до конца'
        sheet['K1'] = 'Приоритет'
        wb.save(filename='result/result.xlsx')
    wb = openpyxl.load_workbook('result/result.xlsx')
    result = db.get_result(peer_id)
    sheet = wb.active
    sheet.append((
        (result.name, result.vk_name, *form_result_string(result.result), result.priority)
    ))
    wb.save('result/result.xlsx')


def save_picture(peer_id, db: DbConnector):
    result = db.get_result(peer_id)
    data_dict = {res.split(': ')[0]: [int(res.split(': ')[1][:-1])] for res in result.result.split(';')[:-1]}
    y_limit = ceil(max(data_dict.values())[0] / 10)
    y_ticks = [i * 10 for i in range(1, y_limit)]
    df = pd.DataFrame({'group': ['A'], **data_dict})

    categories = list(df)[1:]
    ln = len(categories)

    values = df.loc[0].drop('group').values.flatten().tolist()
    values += values[:1]

    angles = [n / float(ln) * 2 * pi for n in range(ln)]
    angles += angles[:1]

    ax = plt.subplot(111, polar=True)

    plt.xticks(angles[:-1], categories, color='grey', size=8)

    ax.set_rlabel_position(0)
    plt.yticks(y_ticks, map(str, y_ticks), color="grey", size=7)
    plt.ylim(0, y_limit * 10)

    ax.plot(angles, values, linewidth=1, linestyle='solid')

    ax.fill(angles, values, 'b', alpha=0.1)

    if not os.path.exists(f"result/{result.peer_id}_{result.vk_name.replace(' ', '')}"):
        os.mkdir(f"result/{result.peer_id}_{result.vk_name.replace(' ', '')}")

    plt.savefig(f"result/{result.peer_id}_{result.vk_name.replace(' ', '')}/graph.png")
    plt.close()

    return f"result/{result.peer_id}_{result.vk_name.replace(' ', '')}/graph.png"


def calculate_test(peer_id, db: DbConnector):
    result_dict = {}
    data = json.loads(db.get_user(peer_id).json_points)
    for alias, schema in pattern.items():
        result_dict[alias] = 0
        for phase, question in schema.items():
            result_dict[alias] += data[str(phase)][str(question)]

    write_result(result_dict, peer_id, db)
    write_excel(peer_id, db)
    pic_path = save_picture(peer_id, db)

    result = db.get_result(peer_id)
    result_string = json.loads(open('static/result.json').read())['result']
    for i, rec in enumerate(result.result.split(';')):
        result_string = result_string.replace('field' + str(i), rec)

    result_string = result_string.replace('field8', result.priority)

    return result_string, pic_path
