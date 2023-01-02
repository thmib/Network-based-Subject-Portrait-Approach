# this file translate edge list of names to edge list of indexes

import sys
import pandas as pd

if __name__ == '__main__':
    add_edge_list = sys.argv[1]
    add_data = sys.argv[2]

    # read edge list
    df_edge_list = pd.read_csv(add_edge_list, sep=',', header=None)
    edge_list_from = df_edge_list.iloc[:, 0]
    edge_list_to = df_edge_list.iloc[:, 1]

    # read data
    df_data = pd.read_csv(add_data)
    column_names = list(df_data.columns)
    
    # get the index of the name
    edge_list_from_index = [column_names.index(from_name) for from_name in edge_list_from]
    edge_list_to_index = [column_names.index(to_name) for to_name in edge_list_to]

    df_out = pd.DataFrame({'from': edge_list_from_index, 'to': edge_list_to_index})
    df_out.to_csv('edge_list_index.csv', index=False, header=False)
