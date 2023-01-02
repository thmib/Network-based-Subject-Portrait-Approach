# This sh file perform machine learning analysis.

#### Parameters ####
cutoff=0.0208 # information gain cutoff
cutoff_comp=60 # the minimun size of network components
num_folds=5 # number of folds for cross validation
seed=25 # random seed

add_input_delta=../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/datasets_deltaDegree
add_input_ori=../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/datasets_ori
add_input=../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/datasets
add_out=../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/machineLearningAnalysis
mkdir -p $add_out

#### Analysis deltaDegree dataset ####
echo "Analysis datasets with delta degree!"
cp $add_input_delta/Allnodes* .

for i in $(seq 1 $num_folds)
do
    add_training_data=Allnodes_train_fold_"$i"_deltaDegree.csv
    add_testing_data=Allnodes_test_fold_"$i"_deltaDegree.csv
    # Training performance
    python LogisticRegressionAnalysis.py $add_training_data $add_training_data $add_training_data.logisticRegression_report.csv 
    python DecisionTreeAnalysis.py $add_training_data $add_training_data $add_training_data.decisionTree_report.csv
    python RandomForestAnalysis.py $add_training_data $add_training_data $add_training_data.randomForest_report.csv

    # Testing performance
    python LogisticRegressionAnalysis.py $add_training_data $add_testing_data $add_testing_data.logisticRegression_report.csv 
    python DecisionTreeAnalysis.py $add_training_data $add_testing_data $add_testing_data.decisionTree_report.csv
    python RandomForestAnalysis.py $add_training_data $add_testing_data $add_testing_data.randomForest_report.csv

    # remove files
    rm $add_training_data
    rm $add_testing_data
done

echo "Summary performance of all feature datasets with delta degree!"
for x in train test
do
    for y in logisticRegression_report decisionTree_report randomForest_report
    do
        echo "Summrize $x performance of all feature datasets with delta degree based on $y!"
        ls *"$x"*"$y"*
        python summarize_performance.py Allnodes_delta_"$x"_"$y"_report.csv *"$x"*"$y"*
        rm *"$x"*"fold_"*"$y"*
    done
done
mv Allnodes_*_report.csv $add_out

#### Analysis origional dataset ####
echo "Analysis datasets with origional features!"
cp $add_input_ori/Allnodes* .

for i in $(seq 1 $num_folds)
do
    add_training_data=Allnodes_train_fold_"$i".csv
    add_testing_data=Allnodes_test_fold_"$i".csv
    # Training performance
    python LogisticRegressionAnalysis.py $add_training_data $add_training_data $add_training_data.logisticRegression_report.csv 
    python DecisionTreeAnalysis.py $add_training_data $add_training_data $add_training_data.decisionTree_report.csv
    python RandomForestAnalysis.py $add_training_data $add_training_data $add_training_data.randomForest_report.csv

    # Testing performance
    python LogisticRegressionAnalysis.py $add_training_data $add_testing_data $add_testing_data.logisticRegression_report.csv 
    python DecisionTreeAnalysis.py $add_training_data $add_testing_data $add_testing_data.decisionTree_report.csv
    python RandomForestAnalysis.py $add_training_data $add_testing_data $add_testing_data.randomForest_report.csv

    # remove files
    rm $add_training_data
    rm $add_testing_data
done

echo "Summary performance of all feature datasets with origional value!"
for x in train test
do
    for y in logisticRegression_report decisionTree_report randomForest_report
    do
        echo "Summrize $x performance of all feature datasets with origional value based on $y!"
        ls *"$x"*"$y"*
        python summarize_performance.py Allnodes_ori_"$x"_"$y"_report.csv *"$x"*"$y"*
        rm *"$x"*"fold_"*"$y"*
    done
done
mv Allnodes_*_report.csv $add_out

#### Cleaning ####
