import csv
from datetime import datetime, timedelta

import matplotlib.pyplot as plt

month_length = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
year_length = [366, 365, 365, 365, 366, 365, 365, 365, 366, 365, 365, 365, 366, 365, 365, 365]


def loadCSV(file, column):
    with open(file, "r") as f:
        content = [row for row in csv.reader(f)]
        header = content[0]
        index = header.index(column)
        content = content[1:]

        dates = [datetime.strptime(row[1].split(" ")[0], r"%Y-%m-%d") for row in content]
        data = [row[index] for row in content]
    return dates, data


def getWeeklyArray(file, column, weekly_average=False):
    dates, data = loadCSV(file, column)
    array_data: dict[int: dict[int: int]] = {}

    current_date = dates[0]
    week_id: int = 0

    while current_date < dates[-1]:
        if current_date.day == 1 and current_date.month == 1:
            week_id = (0 if current_date.weekday() == 0 else 1)

        if current_date.weekday() == 0:
            week_id += 1

        if current_date.year not in array_data:
            array_data[current_date.year] = {}

        if week_id not in array_data[current_date.year]:
            array_data[current_date.year][week_id] = {}

        try:
            if weekly_average:
                week = array_data[current_date.year][week_id]
                if 3 not in week:
                    week[3] = {"count": 0, "value": 0}
                week[3]["count"] += 1
                week[3]["value"] += float(data[dates.index(current_date)])
            else:
                array_data[current_date.year][week_id][current_date.weekday()] = float(data[dates.index(current_date)])
        except ValueError:
            ...

        current_date += timedelta(days=1)

    if weekly_average:
        for year in array_data:
            for week in array_data[year]:
                value = array_data[year][week][3]
                array_data[year][week][3] = value["value"] / value["count"]

    return array_data


def getArray(file, column, month_average=False):
    dates, data = loadCSV(file, column)
    array_data: dict[int: dict[int: dict[int: int]]] = {}

    for i, day in enumerate(dates):
        if day.year not in array_data:
            array_data[day.year] = dict()

        if day.month not in array_data[day.year]:
            array_data[day.year][day.month] = dict()

        try:
            if month_average:
                month_index = int(month_length[day.month - 1] / 2)
                if month_index not in array_data[day.year][day.month].keys():
                    array_data[day.year][day.month][month_index] = {"count": 0, "value": 0}
                array_data[day.year][day.month][month_index]["count"] += 1
                array_data[day.year][day.month][month_index]["value"] += float(data[i])
            else:
                array_data[day.year][day.month][day.day] = float(data[i])
        except ValueError:
            ...

    if month_average:
        for year in array_data:
            for month in array_data[year]:
                value = array_data[year][month][int(month_length[month - 1] / 2)]
                array_data[year][month][int(month_length[month - 1] / 2)] = value["value"] / value["count"]

    return array_data


def plotStackingArray(array_data: dict[int: dict[int: dict[int: int]]], colormap, typ: str = "month"):
    fig, ax = plt.subplots(figsize=(10, 6))

    index = 0
    for year, data in array_data.items():
        color = getattr(plt.cm, colormap)(index / len(array_data))
        x_map = []
        y_map = []

        for mi, month in data.items():
            for di, day in month.items():
                try:
                    if typ == "month":
                        y_map.append(day)
                        x_map.append(sum(month_length[:mi - 1]) + di)
                    elif typ == "week":
                        y_map.append(day)
                        x_map.append((mi - 1) * 7 + di)
                except ValueError:
                    continue

        ax.plot(x_map, y_map, color=color)
        index += 1

    ax.set_xlim(0, 366)
    ax.set_ylim(0, 350)

    ax.set_ylabel("Schneehöhe in cm")

    m_d = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    m_x = [sum(month_length[:i]) + month_length[i] / 2 for i in range(0, 12)]
    ax.set_xticks(m_x)
    ax.set_xticklabels(m_d)

    sm = plt.cm.ScalarMappable(cmap=colormap, norm=plt.Normalize(vmin=min(list(array_data.keys())), vmax=max(list(array_data.keys()))))
    plt.colorbar(sm, ax=ax)

    plt.show()


def plotArray(array_data: dict[int: dict[int: dict[int: int]]]):
    x_map = []
    y_map = []

    for yi, year in array_data.items():
        for mi, month in year.items():
            for di, day in month.items():
                y_map.append(day)
                x_map.append(sum(year_length[:yi - 2008]) + sum(month_length[:mi - 1]) + di)

    plt.plot(x_map, y_map)
    plt.show()


if __name__ == "__main__":
    array = getArray("VAL2.csv", "HS")
    plotStackingArray(array, "Blues")
