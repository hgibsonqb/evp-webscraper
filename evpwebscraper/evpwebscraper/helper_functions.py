import sys
from csv import DictReader

def read_in_data(data_file_in):
    towns = []
    try:
        csvfile = open(data_file_in, 'r')
        reader = DictReader(csvfile)
        for row in reader:
            towns.append(row)
    except FileNotFoundError as e:
        print(str(e))
    return towns
