# This file merge data subsets into one file.
# Parameters:
# 1. Output data file
# 2-end. Input data subset files

import pandas as pd
import sys

def process_file(file):
    df = pd.read_csv(file, sep=',')
    labels = df['Labels'].tolist()
    # delete the column 'Labels'
    df = df.drop('Labels', axis=1)
    return df, labels

if __name__ == "__main__":
    # get the input data subset files
    list_input_files = sys.argv[2:]
    add_output_file = sys.argv[1]

    labels = []
    df = pd.DataFrame()

    for file in list_input_files:
        df_temp, labels_temp = process_file(file)
        labels = labels_temp
        df = pd.concat([df, df_temp], axis=1)
    
    # add labels to the end of df
    df['Labels'] = labels
    # save to file
    df.to_csv(add_output_file, index=False)