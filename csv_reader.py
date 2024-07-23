# -*- coding: utf-8 -*-
"""
date of creation:   06.06.2024
filename:           csv_reader.py
coded by:           Flyingfoxi
"""

import os
from datetime import date


def read_file(file: str) -> tuple[list, list]:
    with open(file, "r") as f:
        content = f.read()
    data = [d.split(",") for d in content.split("\n") if d]
    return data[1:], data[0]


def write_file(data: list[list[str]], file: str) -> None:
    with open(file, "w") as f:
        values = "\n".join([",".join(dat) for dat in data])
        f.write(values)


def edit_file(name: str, required_data: list[str], time_stamp="12:00:00+00:00"):
    data, header = read_file(name)

    year_count = list(range(2008, 2024))
    used_index = [header.index(i) for i in required_data]
    new_data = [[header[i] for i in used_index]]

    for dat in data:
        if (dat[header.index("measure_date")].split(" ")[1] == time_stamp) and (
                int(date(*[int(d) for d in dat[header.index("measure_date")].split(" ")[0].split("-")]).year) in year_count):
            new_data.append([dat[i] for i in used_index])

    write_file(new_data, "data/" + name.split("/")[1])


if __name__ == '__main__':
    required = ["station_code", "measure_date", "TA_30MIN_MEAN", "DW_30MIN_MEAN", "HS"]
    for file_name in os.listdir("raw/"):
        print("file: ", file_name)
        edit_file("raw/" + file_name, required)
