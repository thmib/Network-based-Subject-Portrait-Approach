# This sh file perform feature transformation based on NSPA.

#### Parameters ####
cutoff=0.0272 # information gain cutoff
cutoff_comp=20 # the minimun size of network components
num_folds=5 # number of folds for cross validation
seed=25 # random seed

add_input=../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/datasets
add_input_net=../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/network
add_output=../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/datasets_deltaDegree
add_output_ori=../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/datasets_ori
mkdir $add_output
mkdir $add_output_ori

#### Split the dataset ####

echo "Split the dataset"

cp $add_input/Allnodes* .
python crossvalidation_split.py Allnodes.training.csv $num_folds $seed

#### Feature transformation ####

# translate edge list of names to edge list of indices
echo "Translate edge list of names to edge list of indices"
cp $add_input_net/Alledges.edgelist .
python translate_edge_list.py Alledges.edgelist Allnodes.training.csv

# compute the delta degree of each dataset
echo "Compute the delta degrees of traning dataset"
head -n 1 Allnodes.training.csv > header.csv # prepare the header
tail -n +2 Allnodes.testing.csv > Allnodes.testing.csv.noheader.csv # remove the header
python csv2tsv.py Allnodes.testing.csv.noheader.csv Allnodes.testing.csv.noheader.tsv
rm Allnodes.testing.csv.noheader.csv
for i in $(seq 1 $num_folds)
do
    echo "Fold $i"
    # process test dataset
    python SubjectNetwork_FeatureTransformation.py train_fold_$i.tsv edge_list_index.csv test_fold_$i.tsv
    cp FeatrueTrans.csv test_fold_"$i"_deltaDegree.csv
    cat header.csv test_fold_"$i"_deltaDegree.csv > Allnodes_test_fold_"$i"_deltaDegree.csv
    rm test_fold_"$i"_deltaDegree.csv
    # process train dataset
    python SubjectNetwork_FeatureTransformation.py train_fold_$i.tsv edge_list_index.csv train_fold_$i.tsv
    cp FeatrueTrans.csv train_fold_"$i"_deltaDegree.csv
    cat header.csv train_fold_"$i"_deltaDegree.csv > Allnodes_train_fold_"$i"_deltaDegree.csv
    rm train_fold_"$i"_deltaDegree.csv
    # process validation dataset
    python SubjectNetwork_FeatureTransformation.py train_fold_$i.tsv edge_list_index.csv Allnodes.testing.csv.noheader.tsv
    cp FeatrueTrans.csv validation_fold_"$i"_deltaDegree.csv
    cat header.csv validation_fold_"$i"_deltaDegree.csv > Allnodes_validation_fold_"$i"_deltaDegree.csv
    rm validation_fold_"$i"_deltaDegree.csv
done
rm FeatrueTrans.csv

#### Extract LCs from the delta degree dataset ####
echo "Extract LCs from the delta degree dataset"
# get the nodelist of LCs
cp $add_input_net/LC*.nodelist .
for nodelist in LC*.nodelist
do
    echo "Process LC: $nodelist"
    #get the name of LC
    LC_name=$(echo $nodelist | cut -d'.' -f1)
    for i in $(seq 1 $num_folds)
    do
        python extractSNPsFromDataSubset.py Allnodes_train_fold_"$i"_deltaDegree.csv $nodelist "$LC_name"_train_fold_"$i"_deltaDegree.csv
        python extractSNPsFromDataSubset.py Allnodes_test_fold_"$i"_deltaDegree.csv $nodelist "$LC_name"_test_fold_"$i"_deltaDegree.csv
        python extractSNPsFromDataSubset.py Allnodes_validation_fold_"$i"_deltaDegree.csv $nodelist "$LC_name"_validation_fold_"$i"_deltaDegree.csv
    done
done

#### Extract LCs from the origional dataset ####

echo "Extract LCs from the origional dataset"

for i in $(seq 1 $num_folds)
do
    python tsv2csv.py train_fold_$i.tsv train_fold_$i.noheader.csv
    rm train_fold_$i.tsv
    python tsv2csv.py test_fold_$i.tsv test_fold_$i.noheader.csv
    rm test_fold_$i.tsv
    cat header.csv train_fold_$i.noheader.csv > Allnodes_train_fold_$i.csv
    cat header.csv test_fold_$i.noheader.csv > Allnodes_test_fold_$i.csv
    cat Allnodes.testing.csv > Allnodes_validation_fold_$i.csv
    rm *noheader.csv
done

for nodelist in LC*.nodelist
do
    echo "Process LC: $nodelist"
    #get the name of LC
    LC_name=$(echo $nodelist | cut -d'.' -f1)
    for i in $(seq 1 $num_folds)
    do
        python extractSNPsFromDataSubset.py Allnodes_train_fold_$i.csv $nodelist "$LC_name"_train_fold_"$i".csv
        python extractSNPsFromDataSubset.py Allnodes_test_fold_$i.csv $nodelist "$LC_name"_test_fold_"$i".csv
        python extractSNPsFromDataSubset.py Allnodes.testing.csv $nodelist "$LC_name"_validation_fold_"$i".csv
    done
done


#### Cleaning ####
rm Allnodes.training.csv
rm Allnodes.testing.csv
mv Allnodes*_deltaDegree.csv $add_output # move the transformed datasets to the output folder
mv LC*_deltaDegree.csv $add_output # move the LC specific transformed datasets to the output folder
mv Allnodes*.csv $add_output_ori # move the datasets to the output folder
mv LC*.csv $add_output_ori # move the LC specific datasets to the output folder
rm header.csv
rm edge_list_index.csv
rm LC*.nodelist
rm Allnodes.testing.csv.noheader.tsv