import os
import re
import pandas as pd
import numpy as np
from urllib.parse import urlparse
from load_monkeys import process_mbox
from load_ling import process_and_save_dataset
from preprocess import preprocess_phishing_dataset
from extraction import extract_features

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, f1_score, classification_report

# Define paths
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "data")
mbox_path = os.path.join(data_dir, "phishing3.mbox")

phishing_csv_path = os.path.join(data_dir, "phishing3.csv")
ham_emails_csv_path = os.path.join(data_dir, "ham_emails.csv")
cleaned_csv_path = os.path.join(data_dir, "phishing_emails_cleaned.csv")
features_csv_path = os.path.join(data_dir, "phishing_emails_with_features.csv")

# Step 1: Check if phishing3.csv or ham_emails.csv exist
if not os.path.exists(ham_emails_csv_path):
    print("Ham dataset not found. Running ham email loader...")
    dataset_name = "mandygu/lingspam-dataset"  # Update as needed
    process_and_save_dataset(dataset_name)

if not os.path.exists(phishing_csv_path):
    print("Phishing dataset not found. Running mbox processor...")
    process_mbox(mbox_path, data_dir) 

# Step 2: Check if cleaned CSV exists, if not, preprocess
if not os.path.exists(cleaned_csv_path):
    print("phishing_emails_cleaned.csv not found. Running preprocessing...")
    cleaned_path = preprocess_phishing_dataset(data_dir)  # Pass the correct dataset

    if not cleaned_csv_path:
        print("Preprocessing failed. Exiting.")
        exit(1)

# Step 3: Load cleaned CSV and extract features
if os.path.exists(cleaned_csv_path):
    try:
        df = pd.read_csv(cleaned_csv_path)
        print("Cleaned Dataset Loaded Successfully!")

        df = df.dropna(subset=["body"])  # Drop rows with missing body

        # Ensure "body" is a string to avoid AttributeError
        df["body"] = df["body"].astype(str).fillna("")

        # Step 4: Extract features from the dataset
        feature_df = df.apply(lambda row: extract_features(row), axis=1).apply(pd.Series)

        # Merge features with original dataset
        df_features = pd.concat([df, feature_df], axis=1)

        # Save the features to a CSV
        df_features.to_csv(features_csv_path, index=False)

        print("Feature extraction completed!")
        print(df_features.head())

    except FileNotFoundError:
        print(f"Error: CSV file not found at {cleaned_csv_path}")
        exit(1)

# Step 5: Load the features CSV and prepare for training
try:
    df = pd.read_csv(features_csv_path)

    # Define features and labels
    feature_columns = [
        'num_words', 'num_chars', 'num_uppercase', 'num_special_chars',
        'num_urls', 'num_shortened_urls', 'url_avg_length', 'url_contains_numbers',
        'num_suspicious_keywords',
        'suspicious_word_ratio', 'subject_contains_suspicious_word'
    ]

    X = df[feature_columns]
    print("Feature columns used for training:")
    print(X.columns)
    y = df['label'].astype(int)

    # Split into training and testing sets (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Step 6: Scale features (important for Logistic Regression)
    scaler = StandardScaler()
    X_train = X_train.apply(pd.to_numeric, errors='coerce')
    X_train.fillna(0, inplace=True)
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Step 7: Train and evaluate Logistic Regression
    print("=== Logistic Regression ===")
    lr_model = LogisticRegression()
    lr_model.fit(X_train, y_train)
    lr_pred = lr_model.predict(X_test)

    lr_accuracy = accuracy_score(y_test, lr_pred)
    lr_f1 = f1_score(y_test, lr_pred)

    print(f"Model Accuracy: {lr_accuracy:.2f}")
    print(f"F1 Score: {lr_f1:.2f}")
    print("\nClassification Report:\n", classification_report(y_test, lr_pred))

    # Step 8: Train and evaluate Random Forest
    print("\n=== Random Forest Classifier ===")
    rf_model = RandomForestClassifier(random_state=42)
    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)

    rf_accuracy = accuracy_score(y_test, rf_pred)
    rf_f1 = f1_score(y_test, rf_pred)

    print(f"Model Accuracy: {rf_accuracy:.2f}")
    print(f"F1 Score: {rf_f1:.2f}")
    print("\nClassification Report:\n", classification_report(y_test, rf_pred))

    # Step 9: Train and evaluate Naive Bayes
    print("\n=== Naive Bayes ===")
    nb_model = GaussianNB()
    nb_model.fit(X_train, y_train)
    nb_pred = nb_model.predict(X_test)

    nb_accuracy = accuracy_score(y_test, nb_pred)
    nb_f1 = f1_score(y_test, nb_pred)

    print(f"Model Accuracy: {nb_accuracy:.2f}")
    print(f"F1 Score: {nb_f1:.2f}")
    print("\nClassification Report:\n", classification_report(y_test, nb_pred))
    
except FileNotFoundError:
    print(f"Error: features CSV file not found at {features_csv_path}. Please make sure feature extraction ran correctly.")
    exit(1)
