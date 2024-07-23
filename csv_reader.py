# -*- coding: utf-8 -*-
"""
date of creation:   06.06.2024
filename:           csv_reader.py
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


def edit_file(name: str, required_data: list[str], time_format="%Y%m%d%H", seperator=","):
    data, header = read_file(name, seperator)

    year_count = list(range(2008, 2024))
    used_index = [header.index(i) for i in required_data]
    new_data = [[header[i] for i in used_index]]

    for dat in data:
        try:
            time = datetime.datetime.strptime(dat[header.index(required_data[1])], time_format)
            if time.hour == 00 and time.year in year_count:
                new_data.append([dat[i] for i in used_index])
        except ValueError:
            ...

    write_file(new_data, "data/" + name.split("/")[1])


def read_niederschlag(file: str, required: list[str]):
    edit_file(file, required, seperator=";")

    data, header = read_file("data/" + file.split("/")[1])
    new_data = {
        "JUL2": [["station_code", "measure_date", "rre024i0"]],
        "URS2": [["station_code", "measure_date", "rre024i0"]]
    }

    for dat in data:
        station_code = "JUL2" if "JU2" in dat[0] else "URS2" if "UR2" in dat[0] else "N/A"
        parsed_date = datetime.datetime.strptime(dat[1], "%Y%m%d%H")
        parsed_date.replace(tzinfo=datetime.timezone.utc)
        parsed_date -= datetime.timedelta(hours=12)
        if parsed_date.year == 2007: continue
        measure_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S%z")
        rre024i0 = dat[2]
        match station_code:
            case "JUL2":
                new_data["JUL2"].append([station_code, measure_date, rre024i0])
            case "URS2":
                new_data["URS2"].append([station_code, measure_date, rre024i0])

    write_file(new_data["URS2"], "data/rre024i0/URS2.csv")
    write_file(new_data["JUL2"], "data/rre024i0/JUL2.csv")

    os.remove("data/" + file.split("/")[1])




if __name__ == '__main__':
    read_niederschlag("raw/niederschlag.csv", ["stn", "time", "rre024i0"])
