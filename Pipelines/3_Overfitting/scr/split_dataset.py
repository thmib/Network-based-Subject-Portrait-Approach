# this file read data from the original dataset and split it into train, test and validation set
# input: original dataset, test set size, and random seed
# output: train (###.train.csv), test set (###.test.csv)
import sys
import pandas as pd
from sklearn.model_selection import train_test_split

if __name__ == "__main__":
    # Read the data
    df = pd.read_csv(sys.argv[1])
    # Read Test set size
    test_size = float(sys.argv[2])
    # read random state
    random_state = int(sys.argv[3])

    # get delete path from file name
    file_name = sys.argv[1].split("/")[-1]
    print(file_name)
    

    # get X and y
    X = df.drop('Labels', axis=1)
    y = df['Labels']

    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)

    # add the labels to the train and test data
    X_train['Labels'] = y_train
    X_test['Labels'] = y_test

    # save the data
    X_train.to_csv(sys.argv[4]+str(file_name), index=False)
    X_test.to_csv(sys.argv[5]+str(file_name), index=False)
