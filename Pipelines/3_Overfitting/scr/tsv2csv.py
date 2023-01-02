import pandas as pd
import sys

if __name__ == "__main__":
    add_data= sys.argv[1]
    # read dataset
    data = pd.read_csv(add_data, sep='\t', header=None)
    data.to_csv(sys.argv[2], sep = ',', index=False, header=False)