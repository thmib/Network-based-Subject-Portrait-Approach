# This sh file perform machine learning analysis for LC specific datasets.

#### Parameters ####
cutoff=0.0262 # information gain cutoff
cutoff_comp=50 # the minimun size of network components
num_folds=5 # number of folds for cross validation
seed=25 # random seed

add_input_net=../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/network
add_input_delta=../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/datasets_deltaDegree
add_input_ori=../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/datasets_ori

add_out=../res/igCutoff_"$cutoff"_minCompSize_"$cutoff_comp"/machineLearningAnalysis_LCs
mkdir -p $add_out

num_LCs=$(ls $add_input_net/L*.nodelist | wc -l)
echo "There are $num_LCs LCs!"

#### Analysis deltaDegree datasets ####
echo "Analysis datasets with delta degree!"
for i in $(seq 0 $((num_LCs-1)))
do
    echo "Process LC $i-MachineLearningAnalysis!"
    cp $add_input_delta/LC"$i"_*.csv .
    for j in $(seq 1 $num_folds)
    do
        add_training_data=LC"$i"_train_fold_"$j"_deltaDegree.csv
        add_testing_data=LC"$i"_test_fold_"$j"_deltaDegree.csv
        add_validation_data=LC"$i"_validation_fold_"$j"_deltaDegree.csv
        # Training performance
        python LogisticRegressionAnalysis.py $add_training_data $add_training_data $add_training_data.logisticRegression_report.csv 
        python DecisionTreeAnalysis.py $add_training_data $add_training_data $add_training_data.decisionTree_report.csv
        python RandomForestAnalysis.py $add_training_data $add_training_data $add_training_data.randomForest_report.csv

        # Testing performance
        python LogisticRegressionAnalysis.py $add_training_data $add_testing_data $add_testing_data.logisticRegression_report.csv 
        python DecisionTreeAnalysis.py $add_training_data $add_testing_data $add_testing_data.decisionTree_report.csv
        python RandomForestAnalysis.py $add_training_data $add_testing_data $add_testing_data.randomForest_report.csv

        # Validation performance
        python LogisticRegressionAnalysis.py $add_training_data $add_validation_data $add_validation_data.logisticRegression_report.csv 
        python DecisionTreeAnalysis.py $add_training_data $add_validation_data $add_validation_data.decisionTree_report.csv
        python RandomForestAnalysis.py $add_training_data $add_validation_data $add_validation_data.randomForest_report.csv

        # remove files
        rm $add_training_data
        rm $add_testing_data
        rm $add_validation_data
    done

    echo "Summary performance of all feature datasets with delta degree!"
    for x in train test validation
    do
        for y in logisticRegression_report decisionTree_report randomForest_report
        do
            echo "Summrize $x performance of all feature datasets with delta degree based on $y!"
            ls *"$x"*"$y"*
            python summarize_performance.py LC"$i"_delta_"$x"_"$y"_report.csv *"$x"*"$y"*
            rm *"$x"*"fold_"*"$y"*
        done
    done
    mv LC"$i"_*_report.csv $add_out
done



#### Analysis origional datasets ####
echo "Analysis datasets with delta degree!"
for i in $(seq 0 $((num_LCs-1)))
do
    echo "Process LC $i-MachineLearningAnalysis!"
    cp $add_input_ori/LC"$i"_*.csv .
    for j in $(seq 1 $num_folds)
    do
        add_training_data=LC"$i"_train_fold_"$j".csv
        add_testing_data=LC"$i"_test_fold_"$j".csv
        add_validation_data=LC"$i"_validation_fold_"$j".csv
        # Training performance
        python LogisticRegressionAnalysis.py $add_training_data $add_training_data $add_training_data.logisticRegression_report.csv 
        python DecisionTreeAnalysis.py $add_training_data $add_training_data $add_training_data.decisionTree_report.csv
        python RandomForestAnalysis.py $add_training_data $add_training_data $add_training_data.randomForest_report.csv

        # Testing performance
        python LogisticRegressionAnalysis.py $add_training_data $add_testing_data $add_testing_data.logisticRegression_report.csv 
        python DecisionTreeAnalysis.py $add_training_data $add_testing_data $add_testing_data.decisionTree_report.csv
        python RandomForestAnalysis.py $add_training_data $add_testing_data $add_testing_data.randomForest_report.csv

        # Validation performance
        python LogisticRegressionAnalysis.py $add_training_data $add_validation_data $add_validation_data.logisticRegression_report.csv 
        python DecisionTreeAnalysis.py $add_training_data $add_validation_data $add_validation_data.decisionTree_report.csv
        python RandomForestAnalysis.py $add_training_data $add_validation_data $add_validation_data.randomForest_report.csv

        # remove files
        rm $add_training_data
        rm $add_testing_data
        rm $add_validation_data
    done

    echo "Summary performance of all feature datasets with delta degree!"
    for x in train test validation
    do
        for y in logisticRegression_report decisionTree_report randomForest_report
        do
            echo "Summrize $x performance of all feature datasets with delta degree based on $y!"
            ls *"$x"*"$y"*
            python summarize_performance.py LC"$i"_ori_"$x"_"$y"_report.csv *"$x"*"$y"*
            rm *"$x"*"fold_"*"$y"*
        done
    done
    mv LC"$i"_*_report.csv $add_out
done

#### Visualize the performance of all feature datasets ####

echo "Visualize the performance of all feature datasets!"
mv $add_out/LC*report.csv .
mkdir -p $add_out/detialed_performance
for f in delta ori
do
    for model in logisticRegression_report decisionTree_report randomForest_report
    do
        for cohort in train test validation
        do
            echo "Visualize the performance of $f datasets based on $model for the $cohort cohort!"
            ls LC*"$f"*"$cohort"*"$model"*
            python Summarize_LC_performance.py Summary_"$f"_"$model"_"$cohort".csv LC*"$f"*"$cohort"*"$model"*
            mv LC*"$f"*"$cohort"*"$model"* $add_out/detialed_performance
        done
        echo "Summrize the performace of $f datasets based on $model across all cohorts!"
        python Summarize_cohort_performance.py Summary_"$f"_"$model"_allCohorts.csv Summary_"$f"_"$model"_train.csv Summary_"$f"_"$model"_test.csv Summary_"$f"_"$model"_validation.csv
        mv Summary_"$f"_"$model"_allCohorts.csv $add_out
        mv Summary_"$f"_"$model"_*.csv $add_out/detialed_performance
    done
done