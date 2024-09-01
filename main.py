# -*- coding: utf-8 -*-
"""
date of creation:   06.06.2024
filename:           csv_reader.py
coded by:           Flyingfoxi
"""

import csv
import os
from datetime import datetime, timedelta
from typing import Dict, Iterable, List

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colormaps
from matplotlib.colors import ListedColormap
from pydantic import BaseModel

month_length = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
year_length = [366, 365, 365, 365, 366, 365, 365, 365, 366, 365, 365, 365, 366, 365, 365, 365]

font_header = {"style": "normal", "name": "Arial", "size": 18}
font_labeling = {"style": "normal", "name": "Arial", "size": 14}
font_ticks = {"style": "italic", "name": "Arial", "size": 10}

__all__ = ["Array", "plotArray", "getArray"]


class Array(BaseModel):
    typ: str
    name: str
    data: Dict[int, Dict[int, Dict[int, int]]] | Dict[int, Dict[str, List[float]]]  # day-based / point-based
    columns: List[str]
    colormap: str = "Blues"
    plot_typ: str = "stacked"
    display_typ: str


def loadCSV(file, column):
    with open(file, "r") as f:
        content = [row for row in csv.reader(f)]
        header = content[0]
        try:
            index = header.index(column)
        except ValueError as ex:
            raise ValueError(f"Can't find {column} in header: {header}") from ex
        content = content[1:]

        dates = [datetime.strptime(row[1].split(" ")[0], r"%Y-%m-%d") for row in content]
        data = [row[index] for row in content]
    return dates, data


def _getWeekBasedArray(file, column, weekly_average=True) -> Array:
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

    _array = Array(typ="week",
                   name=file.split("/")[-1].split(".")[0],
                   columns=["measure_date", column],
                   data=array_data,
                   display_typ="Woche")

    return _array


def _getDayBasedArray(file, column, month_average=False) -> Array:
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

    _array = Array(typ=("month" if month_average else "day"),
                   name=file.split("/")[-1].split(".")[0],
                   columns=["measure_date", column],
                   data=array_data,
                   display_typ=("monat" if month_average else "tag").capitalize())
    return _array


def _getPointBasedArray(file: str, key, value) -> Array:
    assert ("measure_date" not in (key, value)), "key or value can't be measure_date, use getArray"

    k_datum, k_data = loadCSV(file, key)
    v_datum, v_data = loadCSV(file, value)

    dates = v_datum

    if not len(k_data) == len(v_data) == len(dates):
        raise ValueError

    array_data = {}

    for i, day in enumerate(dates):
        if day.year not in array_data:
            array_data[day.year] = {"x_map": list(), "y_map": list()}

        try:
            array_data[day.year]["y_map"].append(float(v_data[i]))
            array_data[day.year]["x_map"].append(float(k_data[i]))
        except ValueError:
            if len(array_data[day.year]["y_map"]) > len(array_data[day.year]["x_map"]):
                array_data[day.year]["y_map"].remove(array_data[day.year]["y_map"][-1])

    _array = Array(typ="points",
                   name=file.split("/")[-1].split(".")[0],
                   columns=[key, value],
                   data=array_data,
                   display_typ="Tag")
    return _array


def _plotPointArray(array_data: Array, colormap):
    fig, ax = plt.subplots(figsize=(16, 10))

    for yi, year in array_data.data.items():
        color = getattr(plt.cm, colormap)((yi - 2008) / len(array_data.data))
        # noinspection PyTypeChecker
        ax.scatter(year["x_map"], year["y_map"], color=color, label=str(yi), s=3)

    sm = plt.cm.ScalarMappable(cmap=colormap, norm=plt.Normalize(vmin=min(list(array_data.data.keys())), vmax=max(list(array_data.data.keys()))))
    plt.colorbar(sm, ax=ax)

    _xy_labeling(array_data, ax)

    return plt


def _plotStackingArray(array_data: Array, colormap: list):
    array_data.colormap = colormap
    fig, ax = plt.subplots(figsize=(16, 10))

    index = 0
    last = {"x": [], "y": []}

    for year, data in array_data.data.items():
        color = array_data.colormap[index]
        x_map = last["x"]
        y_map = last["y"]
        last = {"x": [], "y": []}

        for mi, month in data.items():
            for di, day in month.items():
                try:
                    if mi == int(len(data)) and array_data.typ == "month":
                        last["y"].append(day)
                        last["x"].append(sum(month_length[:mi - 1]) + di - year_length[year - 2008])
                    y_map.append(day)
                    if array_data.typ in ["month", "day"]:
                        x_map.append(sum(month_length[:mi - 1]) + di)
                    elif array_data.typ == "week":
                        x_map.append((mi - 1) * 7 + di)
                except ValueError as ex:
                    print(ex)

        # get the january of then next year for the smooth transition of years
        if year != list(array_data.data.keys())[-1]:
            for mi, month in array_data.data[year + 1].items():
                for di, day in month.items():
                    try:
                        y_map.append(day)
                        if array_data.typ in ["month", "day"]:
                            x_map.append(sum(month_length[:mi - 1]) + di + year_length[year - 2008])
                        elif array_data.typ == "week":
                            x_map.append((mi - 1) * 7 + di + year_length[year - 2008])
                    except ValueError as ex:
                        print(ex)

        ax.plot(x_map, y_map, color=color)
        index += 1

    _xy_labeling(array_data, ax)

    return plt


def _plotLinearArray(array_data: Array, colormap):
    assert (colormap in colormaps), "colormap must be available in matplotlib.colormap"
    x_map = []
    y_map = []

    fig, ax = plt.subplots(figsize=(24, 8))
    array_data.colormap = colormap
    color = getattr(plt.cm, array_data.colormap)(0.7)
    for yi, year in array_data.data.items():
        for mi, month in year.items():
            for di, day in month.items():
                y_map.append(day)
                if array_data.typ in ("month", "day"):
                    x_map.append(sum(year_length[:yi - 2008]) + sum(month_length[:mi - 1]) + di)
                else:
                    x_map.append(sum(year_length[:yi - 2008]) + (mi - 1) * 7 + di)

    ax.set_xlim(0, 5844)
    x_ticks = [sum(year_length[:i]) for i in range(0, len(year_length) + 1)]
    x_tick_labels = [str(i + 2008) for i in range(0, len(year_length) + 1)]
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_tick_labels)

    _xy_labeling(array_data, ax)

    x = np.array(x_map)
    y = np.array(y_map)

    slope, intercept = np.polyfit(x, y, 1)
    trend_line = slope * x + intercept

    plt.plot(x_map, y_map, color=color)
    plt.plot(x_map, trend_line, color='darkred')

    ax.text(ax.get_xlim()[1] * 0.99, ax.get_ylim()[1] * 0.972, f"Equation of the trend line: y = {slope:.5f}x + {intercept:.2f}", style='italic',
            fontsize=10, bbox={"facecolor": "lightgrey", "alpha": 0.5, "pad": 5}, ha="right", va="top")

    return plt


def plotArray(array_data: Array, colormap: str | list[str], plot_typ: str = "stacked") -> plt:
    assert (plot_typ in ("stacked", "linear")), f"'{plot_typ}' must be either 'stacked' or 'linear'"

    array_data.plot_typ = plot_typ

    if array_data.typ == "points":
        return _plotPointArray(array_data, colormap)

    if plot_typ == "stacked":
        return _plotStackingArray(array_data, colormap)
    else:
        return _plotLinearArray(array_data, colormap)


def getArray(file: str, value: str, key: str = "measure_date", typ: str = "day") -> Array:
    if key != "measure_date":
        return _getPointBasedArray(file, key=key, value=value)

    if typ == "week":
        return _getWeekBasedArray(file, value)
    else:
        return _getDayBasedArray(file, value, bool(typ == "month"))


def _xy_labeling(array_data: Array, ax: plt.Axes) -> None:
    for i, typ in enumerate("xy"):

        enable_ticks = True
        ticks = []
        tick_labels: Iterable | None = None
        label = ""

        match array_data.columns[i]:
            case "HS":
                plt.title("Schneehöhe von " + array_data.name + f" ({array_data.display_typ})", fontdict=font_header)
                label = "Schneehöhe [cm]"
                lim = (0, 350)
                ticks = [i for i in range(0, 400, 50)]
            case "TA_30MIN_MEAN":
                plt.title("Temperatur von " + array_data.name + f" ({array_data.display_typ})", fontdict=font_header)
                label = "Temperatur [°C]"
                lim = (-20, 40)
                ticks = [i for i in range(-20, 50, 10)]
            case "DW_30MIN_MEAN":
                enable_ticks = True
                plt.title("Windrichtung von " + array_data.name + f" ({array_data.display_typ})", fontdict=font_header)
                label = "Windrichtung [°]"
                ticks = [int(i) for i in range(0, 361, 30)]
                tick_labels = [f"Norden - {i}" if i == 0 or i == 360 else
                               f"Osten - {i}" if i == 90 else
                               f"Süden - {i}" if i == 180 else
                               f"Westen - {i}" if i == 270 else
                               f"{i}" for i in ticks]
                lim = (0, 360)
            case "rre024i0":
                plt.title("Niederschlagsmenge von " + array_data.name + f" ({array_data.display_typ})", fontdict=font_header)
                label = "Niederschlagsmenge [mm/Tag]"
                if array_data.typ == "day":
                    lim = (0, 1200)
                    ticks = [i for i in range(0, 1300, 100)]
                elif array_data.typ == "week":
                    lim = (0, 350)
                    ticks = [i for i in range(0, 400, 50)]
                elif array_data.typ == "month":
                    lim = (0, 120)
                    ticks = [i for i in range(0, 130, 10)]
                else:
                    lim = (0, 500)
                    ticks = [i for i in range(0, 501, 75)]

            case "measure_date":
                enable_ticks = True

                if array_data.plot_typ == "stacked":
                    tick_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan']
                    ticks = [sum(month_length[:i]) for i in range(0, 13)]
                    lim = (0, 366)

                    cmap = ListedColormap(array_data.colormap)

                    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(2008, vmax=2024))
                    cb = plt.colorbar(sm, ax=ax)
                    cmap_ticks = [i + 0.5 for i in range(2008, 2024, 1)]
                    cb.ax.set_ylim(2008, 2024)
                    cb.ax.set_yticks(cmap_ticks)
                    cb.ax.set_yticklabels([str(int(i)) for i in cmap_ticks], fontdict=font_ticks)

                else:
                    tick_labels = [str(i) for i in range(2008, 2025)]
                    ticks = [sum(year_length[:i]) for i in range(len(year_length) + 1)]
                    lim = (0, sum(year_length))

            case other:
                raise ValueError(f"'{other}' is not a valid column")

        if enable_ticks:
            getattr(ax, "set_" + typ + "ticks")(ticks)
            if tick_labels is None:
                tick_labels = [str(i) for i in ticks]
            getattr(ax, "set_" + typ + "ticklabels")(tick_labels, fontdict=font_ticks)
        getattr(ax, "set_" + typ + "lim")(lim)
        getattr(ax, "set_" + typ + "label")(label, fontdict=font_labeling)


def create_dir():
    path = "graphs/"
    if not os.path.exists(path):
        os.mkdir(path)
    for typ in ("stacked", "linear"):
        if not os.path.exists(os.path.join(path, typ)):
            os.mkdir(os.path.join(path, typ))
        for field in ("HS", "TA_30MIN_MEAN", "DW_30MIN_MEAN", "rre024i0"):
            if not os.path.exists(os.path.join(path, typ, field)):
                os.mkdir(os.path.join(path, typ, field))
            for type_ in ("day", "week", "month"):
                if not os.path.exists(os.path.join(path, typ, field, type_)):
                    os.mkdir(os.path.join(path, typ, field, type_))

    if not os.path.exists(os.path.join(path, "dependent")):
        os.mkdir(os.path.join(path, "dependent"))
    for type_ in ("HS", "DW_30MIN_MEAN", "rre024i0"):
        if not os.path.exists(os.path.join(path, "dependent", type_)):
            os.mkdir(os.path.join(path, "dependent", type_))


def main():
    import compile_csv
    compile_csv.main()

    create_dir()

    colors = [
        "#1f77b4",  # Blue
        "#ff7f0e",  # Orange
        "#2ca02c",  # Green
        "#d62728",  # Red
        "#9467bd",  # Purple
        "#8c564b",  # Brown
        "#e377c2",  # Pink
        "#7f7f7f",  # Gray
        "#bcbd22",  # Olive
        "#17becf",  # Cyan
        "#1a55b2",  # Darker Blue
        "#ff9896",  # Light Red
        "#98df8a",  # Light Green
        "#c5b0d5",  # Light Purple
        "#ffbb78",  # Light Orange
        "#9edae5"  # Light Cyan
    ]

    # linear and stacked graphs
    dir_ = "data/"
    for field in ("HS", "TA_30MIN_MEAN", "DW_30MIN_MEAN", "rre024i0"):
        for file in os.listdir(dir_):
            if (file == "VAL2.csv" and field == "rre024i0") or "trend" in file:
                continue

            for type_ in ("day", "week", "month"):
                _array = getArray(dir_ + file, field, typ=type_)
                _colormap = ("Blues" if field == "HS" else "Greens" if field == "TA_30MIN_MEAN" else "Oranges" if field == "DW_30MIN_MEAN" else "Reds")

                plotArray(_array, colors, plot_typ="stacked")
                plt.savefig(f"graphs/stacked/{field}/{type_}/{file.split(".")[0]}.png")
                plt.close()

                plotArray(_array, _colormap, plot_typ="linear")
                plt.savefig(f"graphs/linear/{field}/{type_}/{file.split(".")[0]}.png")
                plt.close()

                print(f"saved ::: {field}/{type_}/{file.split(".")[0]}.png as stacked & linear")

            # dependent graphs (on TA_30MIN_MEAN)
            if field != "TA_30MIN_MEAN":
                _array = getArray(file=dir_ + file, value=field, key="TA_30MIN_MEAN", typ="points")
                _colormap = ("Blues" if field == "HS" else "Oranges" if field == "DW_30MIN_MEAN" else "Reds")

                plotArray(_array, _colormap)
                plt.savefig(f"graphs/dependent/{field}/{file.split(".")[0]}.png")
                plt.close()

                print(f"saved ::: {field}/{file.split('.')[0]}.png as dependent")


if __name__ == "__main__":
    main()
