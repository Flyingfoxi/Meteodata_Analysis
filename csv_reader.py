# -*- coding: utf-8 -*-
"""
date of creation:  06.06.2024
filename:           csv_reader.py
coded by:           Foxispythonlab
"""

from datetime import date


def read_file(file: str) -> list:
    with open(file, "r") as f:
        content = f.read()
    data = [d.split(",") for d in content.split("\n") if d]
    return data[1:]


def write_file(data: list[list[str]], file: str) -> None:
    with open(file, "w") as f:
        values = "\n".join([",".join(dat) for dat in data])
        f.write(values)


if __name__ == '__main__':
    data = read_file("VAL2.csv")
    time_index = 1
    year_index = 1
    used_index = [0, 1, 3, 6, 9]
    time_stamp = "12:00:00+00:00"
    year_count = list(range(2008, 2024))

    new_data = [["station_code", "measure_date", "TA_30MIN_MEAN", "DW_30MIN_MEAN", "HS"]]
    for dat in data:
        if (dat[time_index].split(" ")[1] == time_stamp) and (
                int(date(*[int(d) for d in dat[year_index].split(" ")[0].split("-")]).year) in year_count):
            new_data.append([dat[i] for i in used_index])

    write_file(new_data, "VAL2_new.csv")
