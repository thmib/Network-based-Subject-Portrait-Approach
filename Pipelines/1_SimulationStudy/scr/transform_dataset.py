import pandas as pd
import sys

if __name__ == "__main__":
    # read dataset
    data = pd.read_csv(sys.argv[1], sep='\t')
    labels = data['target']
    del data['target']
    data['Labels'] = labels
    data.to_csv(sys.argv[2]+".csv", index=False, sep=',')