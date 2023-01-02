add_data=../data/pmlb
add_results=../res/pmlb

# transform dataset: change target to Labels

mkdir $add_results
mkdir $add_results/transformed_dataset

for f in $add_data/*.tsv
do
    echo $f
    # get the name of the dataset
    name=$(basename $f)
    python transform_dataset.py $f $add_results/transformed_dataset/$name
done

# construct the comprehensive network

mkdir $add_results/comprehensive_networks

for f in $add_results/transformed_dataset/*.csv
do
    echo $f
    # get the name of the dataset
    name=$(basename $f)
    python ComprehensiveNetwork.py $f > $add_results/comprehensive_networks/$name.ig
done