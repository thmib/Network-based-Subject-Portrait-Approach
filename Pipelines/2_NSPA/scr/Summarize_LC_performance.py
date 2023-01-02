# This file summarize the performance of the LCs
# Parameters:
# 1. add of result 
# 2-end. add of inputs

import sys
import pandas as pd

if __name__ == '__main__':
    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    # read the dataframes
    # get the name of the LCs
    LC_names = [(input_file.split('_')[0],input_file) for input_file in input_files]
    # cat the dataframes
    dataframes = []
    for LC_name, input_file in LC_names:
        # read the dataframe
        df = pd.read_csv(input_file, index_col=0)
        # add the name of the LC to the dataframe
        df['LC'] = LC_name
        dataframes.append(df)
    merged_df = pd.concat(dataframes)
    # set LC column as index
    merged_df.set_index('LC', append=True, inplace=True)
    # output the dataframe
    merged_df.to_csv(output_file)