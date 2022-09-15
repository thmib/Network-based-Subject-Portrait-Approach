# File created by Zhendong Sha on 2020-04-05
# This file formulate pairwise models, with the option of permutation test.

import toolbox as tb
import NetworkPortrait as pn
import multiprocessing

### Parameters
add_dataset = "dataset.txt"
add_models = "twoWayModels.txt"

def multiprocessing_func(p):
    data,i,j,labels = p[0], p[1], p[2], p[3]
    return pn.ModelDecomposition(data, i, j, labels)
    

def main():
    # read dataset
    data = tb.readDataFrame(add_dataset)
    
    # get labels
    # last column is phenotypes
    labels = [l[len(l)-1]for l in data]
    d = dict({1:'0',2:'1'})
    labels = [d[label] for label in labels]
    
    # get features
    features = [l[0:len(l)-1]for l in data]
    # set feature index
    feature_index = list(range(0,len(features[0])))
    
    print('f1_i','f1_v','f2_i','f2_v','l','#',sep=',')
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    res = pool.map(multiprocessing_func,[(data, i, j, labels) for i in range(0, len(feature_index)-1) for j in range(i+1, len(feature_index))])
    pool.close()
    print("".join(res))
            
            
if __name__ == "__main__":
    #### Parameters
    add_dataset = "DATA_Features.tsv"
    add_models = "DATA_TwoWayModels.txt"
    main()
