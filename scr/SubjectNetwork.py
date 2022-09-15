# File created by Zhendong Sha on 2020-04-28
# This file formulate subject network.

import toolbox as tb
import NetworkPortrait as pn
import multiprocessing
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

### Parameters
add_data = "dataset.txt"
add_edgesSelection = "edges.txt"
num_of_folds = 1

def main():
    # read dataset
    data = tb.readDataFrame(add_data)
    
    # get labels
    # last column is phenotypes
    labels = [l[len(l)-1]for l in data]
    labels = [int(l) for l in labels]
    
    # set 0 as controls and 1 as cases
    #d = dict({1:'0',2:'1'})
    #labels = [d[label] for label in labels]
    
    # get features
    features = [l[0:len(l)-1]for l in data]
    
    # get edges
    edge_selection = tb.readDataFrame(add_edgesSelection, ',')
    edges = [(int(l[0]), int(l[1])) for l in edge_selection]
    
    # split folders
    X = np.array(features)
    y = np.array(labels)
    #tb.splitDataEvenly(X,y,2)
    #return
    kf = KFold(n_splits=num_of_folds,shuffle=True)
    Fold = 1
    for train_index, test_index in kf.split(X):
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        
        # formulate training set delta degree
        out_training = pn.MakeSubjectNetDataset(X_train, y_train, X_train, y_train, edges)
        df_out_training = pd.DataFrame.from_records(out_training)
        df_out_training['label'] = y_train
        df_out_training.to_csv('SampleNets_'+str(Fold)+'_'+str(num_of_folds)+'_Train'+'.tsv', sep = '\t', index=False)
        
        # formulate testing set delta degree
        out_testing = pn.MakeSubjectNetDataset(X_train, y_train, X_test, y_test, edges)
        df_out_testing = pd.DataFrame.from_records(out_testing)
        df_out_testing['label'] = y_test
        df_out_testing.to_csv('SampleNets_'+str(Fold)+'_'+str(num_of_folds)+'_Test'+'.tsv', sep = '\t', index=False)
        Fold = Fold + 1
        
        
    
            
if __name__ == "__main__":
    #### Parameters
    add_data = "DATA_Features.tsv"
    add_edgesSelection = "DATA_EdgeSelection.tsv" # no header
    num_of_folds = 5
    main()
