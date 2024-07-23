import csv
import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from icecream import ic

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
                array_data[day.year][day.month][month_index]["value"] += int(float(data[i]))
            else:
                array_data[day.year][day.month][day.day] = int(float(data[i]))
        except ValueError:
            ...

    if month_average:
        for year in array_data:
            for month in array_data[year]:
                value = array_data[year][month][int(month_length[month - 1] / 2)]
                array_data[year][month][int(month_length[month - 1] / 2)] = value["value"] / value["count"]

    return array_data


def plotStackingArray(array_data: dict[int: dict[int: dict[int: int]]], colormap, typ: str = "monat"):
    fig, ax = plt.subplots(figsize=(16, 10))

    index = 0
    last = {"x": [], "y": []}

    for year, data in array_data.items():
        color = getattr(plt.cm, colormap)(index / len(array_data))
        x_map = last["x"]
        y_map = last["y"]
        last = {"x": [], "y": []}

        for mi, month in data.items():
            for di, day in month.items():
                try:
                    if mi == int(len(data)) and typ == "monat":
                        last["y"].append(day)
                        last["x"].append(sum(month_length[:mi - 1]) + di - year_length[year - 2008])
                    y_map.append(day)
                    if typ in ["monat", "tag"]:
                        x_map.append(sum(month_length[:mi - 1]) + di)
                    elif typ == "woche":
                        x_map.append((mi - 1) * 7 + di)
                except ValueError as ex:
                    print(ex)

        # get the january of then next year
        if year != list(array_data.keys())[-1]:
            for mi, month in array_data[year + 1].items():
                for di, day in month.items():
                    try:
                        y_map.append(day)
                        if typ in ["monat", "tag"]:
                            x_map.append(sum(month_length[:mi - 1]) + di + year_length[year - 2008])
                        elif typ == "woche":
                            x_map.append((mi - 1) * 7 + di + year_length[year - 2008])
                    except ValueError as ex:
                        print(ex)

        ax.plot(x_map, y_map, color=color)
        index += 1

    ax.set_xlim(0, 366)
    m_d = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    m_x = [sum(month_length[:i]) + month_length[i] / 2 for i in range(0, 12)]
    ax.set_xticks(m_x)
    ax.set_xticklabels(m_d)

    sm = plt.cm.ScalarMappable(cmap=colormap, norm=plt.Normalize(vmin=min(list(array_data.keys())), vmax=max(list(array_data.keys()))))
    plt.colorbar(sm, ax=ax)

    match field:
        case "HS":
            plt.title("Schneehöhe von " + file.split(".")[0] + f" ({typ})")
            plt.ylabel("Schneehöhe [cm]")
            ax.set_ylim(0, 350)
        case "TA_30MIN_MEAN":
            plt.title("Temperatur von " + file.split(".")[0] + f" ({typ})")
            plt.ylabel("Temperatur [°C]")
            ax.set_ylim(-20, 40)
        case "DW_30MIN_MEAN":
            plt.title("Windrichtung von " + file.split(".")[0] + f" ({typ})")
            plt.ylabel("Windrichtung [°]")
            y_ticks = [int(i) for i in range(0, 361, 30)]
            y_tick_labels = [f"Norden - {i}" if i == 0 or i == 360 else
                             f"Osten - {i}" if i == 90 else
                             f"Süden - {i}" if i == 180 else
                             f"Westen - {i}" if i == 270 else
                             f"{i}" for i in y_ticks]
            ax.set_yticks(y_ticks)
            ax.set_yticklabels(y_tick_labels)
            ax.set_ylim(0, 360)
    return plt


def plotArray(array_data: dict[int: dict[int: dict[int: int]]], colormap, typ: str = "monat"):

    x_map = []
    y_map = []
    fig, ax = plt.subplots(figsize=(24, 8))
    color = getattr(plt.cm, colormap)(0.7)
    for yi, year in array_data.items():
        for mi, month in year.items():
            for di, day in month.items():
                y_map.append(day)
                if typ in ("monat", "tag"):
                    x_map.append(sum(year_length[:yi - 2008]) + sum(month_length[:mi - 1]) + di)
                else:
                    x_map.append(sum(year_length[:yi - 2008]) + (mi - 1) * 7 + di)

    ax.set_xlim(0, 5844)
    x_ticks = [sum(year_length[:i]) for i in range(0, len(year_length) + 1)]
    x_tick_labels = [str(i + 2008) for i in range(0, len(year_length) + 1)]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_tick_labels)

    match field:
        case "HS":
            plt.title("Schneehöhe von " + file.split(".")[0] + f" ({typ})")
            plt.ylabel("Schneehöhe [cm]")
            ax.set_ylim(0, 350)
        case "TA_30MIN_MEAN":
            plt.title("Temperatur von " + file.split(".")[0] + f" ({typ})")
            plt.ylabel("Temperatur [°C]")
            ax.set_ylim(-20, 40)
        case "DW_30MIN_MEAN":
            plt.title("Windrichtung von " + file.split(".")[0] + f" ({typ})")
            plt.ylabel("Windrichtung [°]")
            y_ticks = [int(i) for i in range(0, 361, 30)]
            y_tick_labels = [f"Norden - {i}" if i == 0 or i == 360 else
                             f"Osten - {i}" if i == 90 else
                             f"Süden - {i}" if i == 180 else
                             f"Westen - {i}" if i == 270 else
                             f"{i}" for i in y_ticks]
            ax.set_yticks(y_ticks)
            ax.set_yticklabels(y_tick_labels)
            ax.set_ylim(0, 360)

    plt.plot(x_map, y_map, color=color)
    return plt


def create_dir():
    path = "graphs/"
    for f_typ in ("stacked", "linear"):
        if not os.path.exists(os.path.join(path, f_typ)):
            os.mkdir(os.path.join(path, f_typ))
        for f_field in ("HS", "TA_30MIN_MEAN", "DW_30MIN_MEAN"):
            if not os.path.exists(os.path.join(path, f_typ, f_field)):
                os.mkdir(os.path.join(path, f_typ, f_field))
            for f_type in ("tag", "woche", "monat"):
                if not os.path.exists(os.path.join(path, f_typ, f_field, f_type)):
                    os.mkdir(os.path.join(path, f_typ, f_field, f_type))


if __name__ == "__main__":
    create_dir()
    for field in ("HS", "TA_30MIN_MEAN", "DW_30MIN_MEAN"):
        for d_type in ("tag", "woche", "monat"):
            for file in os.listdir("data/"):
                if d_type == "woche":
                    array = getWeeklyArray("data/" + file, field, True)
                else:
                    array = getArray("data/" + file, field, d_type == "monat")

                d_colormap = ("Blues" if field == "HS" else "Greens" if field == "TA_30MIN_MEAN" else "Reds")
                plotStackingArray(array, d_colormap, typ=d_type).savefig(f"graphs/stacked/{field}/{d_type}/{file.split(".")[0]}.png")
                plt.close()
                plotArray(array, d_colormap, typ=d_type).savefig(f"graphs/linear/{field}/{d_type}/{file.split(".")[0]}.png")
                ic(f"saved ::: {field}/{d_type}/{file.split(".")[0]}.png as stacked & linear")
                plt.close()
