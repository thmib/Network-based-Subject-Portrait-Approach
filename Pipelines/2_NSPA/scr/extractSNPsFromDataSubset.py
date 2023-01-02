# This python file extract a list of snps from data subsets.
# Parameters:
# 1. Input data subset file
# 2. Input snp list file
# 3. Output file

import pandas as pd
import sys


if __name__ == "__main__":
    df = pd.read_csv(sys.argv[1], sep=',')
    snp_list = pd.read_csv(sys.argv[2], sep=',', header=None)
    snp_list = snp_list[0].tolist()

    # Extract the columnname from the data subset
    snp_list_subset = df.columns.tolist()

    # delete snp in snp_list_subset that is not in snp_list
    snp_list_subset = [snp for snp in snp_list_subset if snp in snp_list]
    
    # return if snp_list_subset is empty
    if not snp_list_subset:
        print("No SNP in the data subset!")
        sys.exit(0)
    else:
        print("Number of SNP in the data subset: "+str(len(snp_list_subset)))
        # add Labels to snp_list_subset
        snp_list_subset.append('Labels')
        # get columns from df according to snp_list_subset
        df_selected = df[snp_list_subset]
        # add labels to the end of df_selected
        df_selected.to_csv(sys.argv[3], index=False)

    
