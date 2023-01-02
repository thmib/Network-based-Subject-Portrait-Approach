# This file summarize the performance of different cohorts
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
    cohort_names = [(input_file.split('_')[-1],input_file) for input_file in input_files]
    # cat the dataframes
    dataframes = {}
    for cohort_name, input_file in cohort_names:
        # read the dataframe
        cohort_name = cohort_name.split('.')[0]
        df = pd.read_csv(input_file, index_col=[0,1])
        # add the name of the cohort to the dataframes
        dataframes[cohort_name] = df
    # merge the dataframes by columns
    merged_df = pd.concat(dataframes, axis=1)
    # output the dataframe
    merged_df.to_csv(output_file)
