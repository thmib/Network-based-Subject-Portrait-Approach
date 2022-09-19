# Network based subject portrait approach (NSPA)
NSPA converts genetic variants of subjects into new values that capture how genetic variables interact with others to regulate a subject’s disease risk. 
## Required packages
NSPA is written in Python 3. You need to download this repository to local and make sure the following packages have been installed.
* pandas
* numpy
* multiprocessing
* sklearn
* csv
## Analysis phase 1: generate comprehensive network
Sample Run Command:
```
bash Run_BuildComprehensiveNetwork.sh
```
**ComprehensiveNetwork.py** contains one parameter indicating the dataset used to build the network. **ComprehensiveNetwork.tsv** is the output network. The first and second columns are SNP, the third column is information gain, and the fourth column is mutual infordmation. The resulting comprehensive network is fully connected, so some SNP interactions with weak interactions need to be filtered out.
## Analysis phase 2: generate subject networks
Sample Run Command:
```
bash Run_BuildSubjectNetwork.sh
```
This command will produce a 5-fold cross-validation dataset with the transformed features. **SubjectNetwork.py** contains two parameters with the first parameter indicating the dataset and the second paramter indicating the edge list of the comprehensive network. 
## High-performance computation
Although the first step has been parallelized using the multiprocessing package, if the dataset includes hundreds of thousands of SNPs, it is necessary to use high-performance computing to get the results in time. We propose to achieve high-performance computing by data chunking.
The specific steps are.
1. partitioning the high-dimensional data into independent sub-datas by SNP, each sub-data including a less number of SNPs and labels.
2. evaluate all SNP interactions using **ComprehensiveNetwork.py** for each sub-data.
3. evaluate the feature interactions between any pair of sub-datas using **/scr/ComprehensiveNetwork_Bipartisan.py**.
4. merge.
Note that the merged data can be very large. It is recommended that the weakest SNP interactions are removed before merging. This would reduce the overall data size by several orders of magnitude.