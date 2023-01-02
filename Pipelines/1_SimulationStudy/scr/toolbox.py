# This is a toolbox providing necessary utilities.
import csv

def readDataFrame(add, sep = '\t'):
    with open(add) as database:
        Reader = csv.reader(database,delimiter=sep)
        data = list(list(float(elem) for elem in row) for row in Reader)
    return data
