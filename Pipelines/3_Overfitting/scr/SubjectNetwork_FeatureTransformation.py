# This file is used to perform feature transformation based on NSPA
# Parameters:
# 1. add_data_training: the address of the training dataset (no header)
# 2. add_edgesSelection: the address of the selected edges (index)
# 3. add_data_trans: the address of the dataset to perform feature transformation (no header)

import toolbox as tb
import NetworkPortrait as pn
import numpy as np
import pandas as pd
import sys

def getLabels(data):
    # get labels
    # last column is phenotypes
    labels = [l[len(l)-1]for l in data]
    labels = [int(l) for l in labels]
    return np.array(labels)

def getFeatures(data):
    # get features
    features = [l[0:len(l)-1]for l in data]
    return np.array(features)

def getDeltaDegree(X_train, y_train, X_test, y_test, edges):
    # formulate testing set delta degree
    out_testing = pn.MakeSubjectNetDataset(X_train, y_train, X_test, y_test, edges)
    df_out = pd.DataFrame.from_records(out_testing)
    df_out['label'] = y_test
    return df_out

if __name__ == "__main__":
    add_data_training = sys.argv[1]
    add_edgesSelection = sys.argv[2]
    add_data_trans = sys.argv[3]

    # read dataset
    data_training = tb.readDataFrame(add_data_training)
    data_trans = tb.readDataFrame(add_data_trans)
    # get labels of data_training
    data_training_labels = getLabels(data_training) 
    # get features of data_training
    data_training_features = getFeatures(data_training) 
    # get labels of data_trans
    data_trans_labels = getLabels(data_trans)
    # get features of data_trans
    data_trans_features = getFeatures(data_trans)
    
    # read edges
    edge_selection = tb.readDataFrame(add_edgesSelection, ',')
    edge_selection = [(int(l[0]), int(l[1])) for l in edge_selection]

    # formulate data_trans set delta degree
    df_out = getDeltaDegree(data_training_features, data_training_labels, data_trans_features, data_trans_labels, edge_selection)
    df_out.to_csv('FeatrueTrans.csv', sep = ',', index=False, header=False)
