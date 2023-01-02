#### Parameters ####
cutoff=0.0272 # information gain cutoff
cutoff_comp=20 # the minimun size of network components

#### network preparetion ####

# get the edgelist from the res folder

echo "Get the edgelist from the res folder!"

cp ../res/CN_ig_0.015.ig .
python get_edgelist.py CN_ig_0.015.ig $cutoff CN_ig_cutoff_$cutoff.edgelist # select edges by information gain cutoff
rm CN_ig_0.015.ig

# get the network components
python get_network_components.py CN_ig_cutoff_$cutoff.edgelist $cutoff_comp # print list of components size, edge list of each component, and node list of each component
cat LC*.edgelist > Alledges.edgelist # combine all the edge list of components
cat LC*.nodelist > Allnodes.nodelist # combine all the node list of components

#### Training dataset preparation ####

echo "Prepare training dataset!"

cp ../res/gwasSubsets/training/*.data . # move data subsets

for f_subset in *.data
do
    echo "Processing $f_subset file..."
    python extractSNPsFromDataSubset.py $f_subset Allnodes.nodelist $f_subset.temp # extract SNPs from data subset
done
rm *.data
python mergeSelectedDataSubsets.py Allnodes.training.csv *.temp # merge data subsets

rm *.temp

# prepare LC specific training datasets
for f_subset in *.nodelist
do
    echo "Processing $f_subset file..."
    filename=$(basename -- "$f_subset")
    extension="${filename##*.}"
    filename="${filename%.*}"
    python extractSNPsFromDataSubset.py Allnodes.training.csv $f_subset $filename.training.csv # extract SNPs from dataset
done

#### Testing dataset preparation ####

echo "Prepare testing dataset!"

cp ../res/gwasSubsets/testing/*.data . # move data subsets

for f_subset in *.data
do
    echo "Processing $f_subset file..."
    python extractSNPsFromDataSubset.py $f_subset Allnodes.nodelist $f_subset.temp # extract SNPs from data subset
done
rm *.data
python mergeSelectedDataSubsets.py Allnodes.testing.csv *.temp # merge data subsets

rm *.temp

# prepare LC specific testing datasets
for f_subset in *.nodelist
do
    echo "Processing $f_subset file..."
    filename=$(basename -- "$f_subset")
    extension="${filename##*.}"
    filename="${filename%.*}"
    python extractSNPsFromDataSubset.py Allnodes.testing.csv $f_subset $filename.testing.csv # extract SNPs from dataset
done

#### Move files to res folder ####

echo "Move files to res folder!"

mkdir ../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"

# move network information
mkdir ../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/network

mv *.edgelist ../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/network/
mv *.nodelist ../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/network/
mv components_size.csv ../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/network/

# move training and testing datasets
mkdir ../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/datasets

mv LC*.csv ../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/datasets/
mv Allnodes.*.csv ../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/datasets/