# This py file select edge by threshold.
# Parameter list: 
# 1. edgelist
# 2. cutoff

import pandas as pd
import numpy as np
import sys


if __name__ == "__main__":
    # read edgelist 
    add_edgelist = sys.argv[1]
    th=float(sys.argv[2])
    df_edgelist = pd.read_csv(add_edgelist, dtype={'SNP1': str, 'SNP2': str, 'ig': np.float16, 'mi': np.float16}, names = ['SNP1', 'SNP2', 'ig', 'mi'], header=None,delim_whitespace=True)
    df_edgelist = df_edgelist.loc[df_edgelist['ig'] >= th]
    df_edgelist.to_csv(sys.argv[3], header=True, sep='\t',index=False)
