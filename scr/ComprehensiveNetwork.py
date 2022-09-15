# File created by Zhendong Sha on 2020-04-05
# This file formulate pairwise models, with the option of permutation test.

import toolbox as tb
import NetworkPortrait as pn
import sys
import pandas as pd
import multiprocessing

### Parameters
add_dataset = "dataset.txt"
num_permutation = 0

def multiprocessing_func(p):
    data,snp_i,snp_j,labels,num_p = p[0], p[1], p[2], p[3], p[4]
    return pn.ComprehensiveNet(data[snp_i], data[snp_j], snp_i, snp_j, labels, num_p)
    
def processDF(df):
    # get labels
    labels = df['Labels']
    #df.drop(['Labels'], axis=1)
    del df['Labels']

    # get snp names
    features = df.columns

    return labels, features, df


def main():
    # read dataset
    data = pd.read_csv(add_dataset)
    labels, snps, data = processDF(data)

    print('f1_i','f2_i','ig','mutual',sep='\t')
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    edges = [[i,j]for i in range(0, len(snps)-1) for j in range(i+1, len(snps))]
    #pool = multiprocessing.Pool(1)
    io_batch_size = 5000
    while (len(edges) > 0):
        edges_this, edges = edges[:io_batch_size], edges[io_batch_size:]
        res = pool.map(multiprocessing_func,[(data, snps[e[0]], snps[e[1]], labels, num_permutation) for e in edges_this])
        print("".join(res),end='')

    pool.close()
    
            
            
if __name__ == "__main__":
    #### Parameters
    
    #add_dataset = "NLCRC_All2000-3999.data"
    add_dataset = sys.argv[1]
    num_permutation = 0

    main()
