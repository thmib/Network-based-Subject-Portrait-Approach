# This py file perform predictive analysis based on decision tree.
# Parameters:
# 1. Input file (training)
# 2. Input file (prediction)

import sys
import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report
from sklearn.metrics import roc_auc_score

def main():
    # Read training data
    training_data = pd.read_csv(sys.argv[1], sep=',', header=0)
    # Read prediction data
    prediction_data = pd.read_csv(sys.argv[2], sep=',', header=0)
    # Get the features and target of training data
    training_features = training_data.drop('Labels', axis=1)
    training_target = training_data['Labels']
    # Get the features and target of prediction data
    prediction_features = prediction_data.drop('Labels', axis=1)
    prediction_target = prediction_data['Labels']
    # Create a logistic regression model
    model = DecisionTreeClassifier(class_weight='balanced',min_samples_leaf=0.05)
    # Train the model using the training sets and check score
    model.fit(training_features, training_target)
    # Preiictive performance
    # print("Training score: ", model.score(training_features, training_target))
    # print("Testing score: ", model.score(prediction_features, prediction_target))
    # Report the response for prediction data
    prediction_target_predicted = model.predict(prediction_features)
    df = pd.DataFrame(classification_report(prediction_target, prediction_target_predicted, target_names=['control', 'case'],output_dict=True)).transpose()
    df.to_csv(sys.argv[3], sep=',')    

if __name__ == '__main__':
    main()