# -*- coding: utf-8 -*-
"""
date of creation:   06.06.2024
filename:           compile_csv.py
coded by:           Flyingfoxi
"""

import datetime
import os


def read_file(file: str, sep=",") -> tuple[list, list]:
    with open(file, "r") as f:
        content = f.read()
    data = [d.split(sep) for d in content.split("\n") if d]
    return data[1:], data[0]


def write_file(data: list[list[str]], file: str) -> None:
    with open(file, "w") as f:
        values = "\n".join([",".join(dat) for dat in data])
        f.write(values)


def edit_file(name: str, required_data: list[str], time_format="%Y-%m-%d %H:%M:%S%z", seperator=",", save=True):
    data, header = read_file(name, seperator)

    year_count = list(range(2008, 2024))
    used_index = [header.index(i) for i in required_data]
    new_data = [[header[i] for i in used_index]]

    print(len(data))

    for dat in data:
        try:
            time = datetime.datetime.strptime(dat[header.index(required_data[1])], time_format)
            if time.hour == 12 and time.minute == 0 and time.year in year_count:
                new_data.append([dat[i] for i in used_index])
        except ValueError:
            ...

    if save:
        write_file(new_data, "data/" + name.split("/")[1])
    return new_data


def collect_rainfall(file: str, required: list[str]):
    edit_file(file, required, seperator=";", time_format="%Y%m%d%H")

    data, header = read_file("data/" + file.split("/")[1])
    new_data = {
        "JUL2": [["station_code", "measure_date", "rre024i0"]],
        "URS2": [["station_code", "measure_date", "rre024i0"]]
    }

    for dat in data:
        station_code = "JUL2" if "JU2" in dat[0] else "URS2" if "UR2" in dat[0] else "N/A"
        parsed_date = datetime.datetime.strptime(dat[1], "%Y%m%d%H")
        parsed_date = parsed_date.replace(tzinfo=datetime.timezone.utc)
        parsed_date -= datetime.timedelta(hours=12)
        if parsed_date.year == 2007: continue
        measure_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S%z")

        rre024i0 = dat[2]
        match station_code:
            case "JUL2":
                new_data["JUL2"].append([station_code, measure_date, rre024i0])
            case "URS2":
                new_data["URS2"].append([station_code, measure_date, rre024i0])

    os.remove("data/" + file.split("/")[1])

    write_file(new_data["JUL2"], "data/_JUL2.csv")
    write_file(new_data["URS2"], "data/_URS2.csv")

    return new_data


def fuse_files(file1, file2, sep=","):
    def common_elements(a1: list, a2: list):
        return [i for i in a1 if i in a2]

    def fuse_day(a1: list, a2: list) -> list:
        new_line = []
        for h in header:
            if h in _header1:
                new_line.append(a1[_header1.index(h)])
            elif h in _header2:
                new_line.append(a2[_header2.index(h)])
            else:
                raise ValueError("Invalid headers")
        return new_line

    _data1, _header1 = read_file(file1, sep)
    _data2, _header2 = read_file(file2, sep)

    os.remove(file1)
    os.remove(file2)

    header = _header1 + [i for i in _header2 if i not in _header1]
    data = [header]

    assert _data1[0][0] == _data2[0][0], "station code must be the same"

    index_measure_date1 = _header1.index("measure_date")
    index_measure_date2 = _header2.index("measure_date")

    _dict1 = {datetime.datetime.strptime(entry[index_measure_date1], "%Y-%m-%d %H:%M:%S%z").replace(hour=0, minute=0): entry for entry in _data1}
    _dict2 = {datetime.datetime.strptime(entry[index_measure_date2], "%Y-%m-%d %H:%M:%S%z").replace(hour=0, minute=0): entry for entry in _data2}

    common_days = common_elements(list(_dict1.keys()), list(_dict2.keys()))

    for day in common_days:
        data.append(fuse_day(_dict1[day], _dict2[day]))

    write_file(data, file1)
    return header + data


def get_trend(file: str, months: list[int], required: str, time_format="%Y-%m-%d %H:%M:%S%z"):
    content, header = read_file(file)
    index = header.index(required)
    date_index = header.index("measure_date")
    station_code = content[0][header.index("station_code")]

    output = {}

    for data in content:
        try:
            time = datetime.datetime.strptime(data[date_index], time_format)
            if time.month in months:
                output.setdefault(time.year, []).append(float(data[index]))
        except ValueError:
            ...

    compiled = [["station_code", "measure_year", required]]

    for year, values in output.items():
        average = sum(values) / len(values)
        compiled.append([station_code, str(year), str(average)])

    write_file(compiled, "data/trend-" + file.split("/")[1])



def main():
    print("starting to compile ...")
    edit_file("raw/JUL2.csv", ["station_code", "measure_date", "HS", "TA_30MIN_MEAN", "DW_30MIN_MEAN"])
    edit_file("raw/URS2.csv", ["station_code", "measure_date", "HS", "TA_30MIN_MEAN", "DW_30MIN_MEAN"])
    edit_file("raw/VAL2.csv", ["station_code", "measure_date", "HS", "TA_30MIN_MEAN", "DW_30MIN_MEAN"])
    collect_rainfall("raw/niederschlag.csv", ["stn", "time", "rre024i0"])
    get_trend("raw/JUL2.csv", [11, 12, 1, 2, 3, 4], "HS")
    get_trend("raw/VAL2.csv", [11, 12, 1, 2, 3, 4], "HS")
    print("basic completed, fusing the files ...")
    fuse_files("data/JUL2.csv", "data/_JUL2.csv")
    fuse_files("data/URS2.csv", "data/_URS2.csv")
    print("Successfully compiled the files")


if __name__ == '__main__':
    main()
