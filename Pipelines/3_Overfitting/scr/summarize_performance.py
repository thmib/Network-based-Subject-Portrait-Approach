# this file summrize the performance report of different folds.
# Parameters:
# 1. Output file name
# 2. Input file names

import pandas as pd
import sys


if __name__ == '__main__':
    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    dataframes = []
    for input_file in input_files:
        dataframes.append(pd.read_csv(input_file, index_col=0))
    # average the dataframes
    df = pd.concat(dataframes, keys=range(len(dataframes)))
    df = df.groupby(level=1).mean()
    df.to_csv(output_file)
