import numpy as np

def findMode(col):
    values = []
    valuesCount = []
    for value in col:
        if value in values and (value is not None or value is not np.nan):
            index = values.index(value)
            valuesCount[index] += 1
        else:
            values.append(value)
            valuesCount.append(0)
    modeIndex = 0
    for i in range(0, len(values)):
        if valuesCount[i] > valuesCount[modeIndex]:
            modeIndex = i
    return values[modeIndex]

def findUnique(col):
    vals = []
    for value in col:
        if value not in vals and (value is not None or value is not np.nan):
            vals.append(value)
    return vals