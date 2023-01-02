# This py file split the dataset into cross validation folds
# Parameters:
# 1. add_data: the address of the dataset
# 2. num_of_folds: number of folds
# 3. seed: random seed

import sys
import pandas as pd
from sklearn.model_selection import StratifiedKFold

if __name__ == '__main__':
    add_data = sys.argv[1]
    df = pd.read_csv(add_data)
    num_of_folds = int(sys.argv[2])
    seed = int(sys.argv[3])

    # get last column of the df
    y = df.iloc[:, -1]
    # get the rest of the df
    X = df.iloc[:, :-1]

    # stratified k-fold cross validation
    skf = StratifiedKFold(n_splits=num_of_folds, shuffle=True, random_state=seed)
    Fold = 1
    for train_index, test_index in skf.split(X, y):
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        # save the train and test folds
        df_train = pd.concat([X_train, y_train], axis=1)
        df_test = pd.concat([X_test, y_test], axis=1)
        df_train.to_csv('train_fold_' + str(Fold) + '.tsv', index=False, header=False, sep='\t')
        df_test.to_csv('test_fold_' + str(Fold) + '.tsv', index=False, header=False, sep='\t')
        Fold += 1

