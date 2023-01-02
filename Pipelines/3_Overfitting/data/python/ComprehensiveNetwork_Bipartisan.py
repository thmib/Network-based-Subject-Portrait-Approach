# File created by Zhendong Sha on 2020-04-05
# This file formulate pairwise models, with the option of permutation test.

import toolbox as tb
import NetworkPortrait as pn
import sys
import pandas as pd
import multiprocessing

### Parameters
add_dataset_1 = "dataset.txt"
add_dataset_2 = "dataset.txt"
num_permutation = 0

def multiprocessing_func(p):
    data1, data2, snp_i,snp_j,labels,num_p = p[0], p[1], p[2], p[3], p[4], p[5]
    return pn.ComprehensiveNet(data1[snp_i], data2[snp_j], snp_i, snp_j, labels, num_p)
    
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
    data1 = pd.read_csv(add_dataset_1)
    data2 = pd.read_csv(add_dataset_2)
    labels_1, snps_1, data_1 = processDF(data1)
    labels_2, snps_2, data_2 = processDF(data2)

    #print('f1_i','f2_i','ig','mutual',sep='\t')
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    edges = [[i,j]for i in range(0, len(snps_1)) for j in range(0, len(snps_2))]
    #pool = multiprocessing.Pool(1)
    io_batch_size = int(len(edges))
    while (len(edges) > 0):
        edges_this, edges = edges[:io_batch_size], edges[io_batch_size:]
        res = pool.map(multiprocessing_func,[(data1, data2, snps_1[e[0]], snps_2[e[1]], labels_1, num_permutation) for e in edges_this])
        print("".join(res),end='')

    pool.close()
    
            
            
if __name__ == "__main__":
    #### Parameters
    
    #add_dataset = "NLCRC_All2000-3999.data"
    add_dataset_1 = sys.argv[1]
    add_dataset_2 = sys.argv[2]
    num_permutation = 0

    main()
