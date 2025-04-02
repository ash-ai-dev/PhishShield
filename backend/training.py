import os
import re
import pandas as pd
import numpy as np
from urllib.parse import urlparse
from load_datasets import load_and_get_dataset_path  # Import the function
from preprocess import preprocess_phishing_dataset # import preprocess dataset function
from extraction import extract_features

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, classification_report


# Dataset details
dataset_name = "naserabdullahalam/phishing-email-dataset"
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "data")

# Load and get dataset path
dataset_path = load_and_get_dataset_path(dataset_name, data_dir)

cleaned_csv_path = os.path.join(data_dir, "phishing_emails_cleaned.csv")
features_csv_path = os.path.join(data_dir, "phishing_emails_with_features.csv") # define the path for the features csv

if dataset_path:
    # Check if cleaned CSV exists, if not, preprocess.
    if not os.path.exists(cleaned_csv_path):
        print("phishing_emails_cleaned.csv not found. Running preprocessing...")
        cleaned_csv_path = preprocess_phishing_dataset(dataset_path)

        if not cleaned_csv_path:
            print("Preprocessing failed. Exiting.")
            exit(1)

    # Now, load the cleaned CSV and extract features
    try:
        # Check if the cleaned CSV path is correct
        if os.path.exists(cleaned_csv_path) and os.path.basename(cleaned_csv_path) == "phishing_emails_cleaned.csv":
            df = pd.read_csv(cleaned_csv_path)
            print("Cleaned Dataset Loaded Successfully!")

            df = df.dropna(subset=["body"])

            # Ensure "body" is a string to avoid AttributeError
            df["body"] = df["body"].astype(str).fillna("")

            # Extract features from each email
            feature_df = df.apply(lambda row: extract_features(row), axis=1).apply(pd.Series)


            # Merge features with original dataset
            df_features = pd.concat([df, feature_df], axis=1)

            # Save extracted features
            df_features.to_csv(features_csv_path, index=False)

            print("Feature extraction completed!")
            print(df_features.head())
        else:
            print(f"Error: Cleaned CSV file not found or has incorrect name. Expected 'phishing_emails_cleaned.csv'.")
            exit(1)
    except FileNotFoundError:
        print(f"Error: CSV file not found at {cleaned_csv_path}")
        exit(1)
else:
    print("Failed to load dataset. Exiting.")
    exit(1)

# Load the features csv file.
try:
    df = pd.read_csv(features_csv_path)

    # Define features and labels
    X = df[['num_words', 'num_chars', 'num_uppercase', 'num_special_chars',
            'num_urls', 'num_shortened_urls', 'url_avg_length', 'url_contains_numbers',
            'suspicious_domain_count', 'num_encoded_urls', 'num_suspicious_keywords',
            'suspicious_word_ratio', 'subject_length', 'subject_contains_suspicious_word',
            'num_exclamation', 'num_question_marks', 'contains_html',
            'sender_is_free_email', 'sender_email_length', 'sender_has_random_numbers',
        ]]
    y = df['label']  # Assuming 'label' is the phishing (1) or not (0) column

    # Split into training and testing sets (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Scale features (important for Logistic Regression)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Train Logistic Regression Model
    model = LogisticRegression()
    model.fit(X_train, y_train)

    # Make predictions
    y_pred = model.predict(X_test)

    # Evaluate model performance
    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    print(f"Model Accuracy: {accuracy:.2f}")
    print(f"F1 Score: {f1:.2f}")
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

except FileNotFoundError:
    print(f"Error: features csv file not found at {features_csv_path}. Please make sure feature extraction ran correctly.")
    exit(1)