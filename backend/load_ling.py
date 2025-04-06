import os
import re
import pandas as pd
import kagglehub
from dotenv import load_dotenv

def process_and_save_dataset(dataset_name, output_filename="ham_emails.csv"):
    """Downloads and processes the dataset and saves the processed data to a CSV."""
    
    # Load Kaggle API keys from kaggle.env
    load_dotenv(dotenv_path="kaggle.env")
    KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
    KAGGLE_KEY = os.getenv("KAGGLE_KEY")

    # Check if credentials are loaded
    if not KAGGLE_USERNAME or not KAGGLE_KEY:
        print("Kaggle API credentials not found. Please create a kaggle.env file with KAGGLE_USERNAME and KAGGLE_KEY.")
        return
    
    # Download the dataset from Kaggle
    try:
        print("Downloading dataset from Kaggle...")
        dataset_path = kagglehub.dataset_download(dataset_name)
        if not dataset_path:
            print("Dataset download failed.")
            return
        print(f"Dataset downloaded to: {dataset_path}")
    except kagglehub.exceptions.KaggleApiHTTPError as e:
        print(f"Error downloading dataset: {e}")
        return

    # Look for CSV files in the downloaded dataset
    csv_files = [f for f in os.listdir(dataset_path) if f.endswith('.csv')]
    if not csv_files:
        print("No CSV file found in the downloaded dataset.")
        return

    # Process the first CSV file found
    csv_path = os.path.join(dataset_path, csv_files[0])

    # Load and process data
    df = pd.read_csv(csv_path)

    # Check the first few rows to inspect the data
    print(df.head())  # Verify columns and data

    # Filter for 'Ham' examples only
    if 'label' not in df.columns:
        print("Error: 'label' column not found.")
        return

    df = df[df['label'] == 0]  # Assuming '0' represents 'Ham'

    if df.empty:
        print("No 'Ham' examples found.")
        return

    # Define feature extraction functions here or import them if needed
    def extract_features_from_content(subject, body):
        """Extracts various features from the email's subject and body."""
        features = {
            'sender': extract_sender(body),
            'subject': subject,
            'date': extract_date(body),
            'reply_to': extract_reply_to(body),
            'message_id': extract_message_id(body),
            'content_type': 'text/plain',  # Assuming it's plain text as it's not explicitly provided
            'has_attachment': extract_attachment(body),
            'body': body,
            'urls': extract_urls(body),
        }
        return features

    def extract_sender(body):
        sender_pattern = r"(?:From:\s*)([\w\.-]+@[\w\.-]+)"
        match = re.search(sender_pattern, body)
        return match.group(1) if match else None

    def extract_date(body):
        date_pattern = r"(?:Date:\s*)([A-Za-z]{3},\s*\d{1,2}\s*[A-Za-z]{3}\s*\d{4}\s*\d{2}:\d{2}:\d{2}\s*[A-Za-z]{3})"
        match = re.search(date_pattern, body)
        return match.group(1) if match else None

    def extract_reply_to(body):
        reply_to_pattern = r"(?:Reply-To:\s*)([\w\.-]+@[\w\.-]+)"
        match = re.search(reply_to_pattern, body)
        return match.group(1) if match else None

    def extract_message_id(body):
        message_id_pattern = r"(?:Message-ID:\s*)(<.*?>)"
        match = re.search(message_id_pattern, body)
        return match.group(1) if match else None

    def extract_attachment(body):
        attachment_pattern = r"(?:attachment|attached)"
        return bool(re.search(attachment_pattern, body))

    def extract_urls(body):
        url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        return re.findall(url_pattern, body)

    # Add extracted features to the dataframe
    features_list = df.apply(lambda row: extract_features_from_content(row['subject'], row['message']), axis=1)
    features_df = pd.json_normalize(features_list)

    # Combine original dataset with the extracted features
    full_df = pd.concat([df, features_df], axis=1)

    # Remove duplicates based on 'subject' and 'message' columns
    df_cleaned = full_df.drop_duplicates(subset=["subject", "message"], keep="first")

    # Drop the first index (if needed)
    df_cleaned = df_cleaned.drop(index=0)

    # Reorder the columns
    column_order = ['sender', 'subject', 'date', 'reply_to', 'message_id', 'content_type', 'has_attachment', 'body', 'urls', 'label']
    df_cleaned = df_cleaned[column_order]

    # Check combined dataframe before saving
    print(df_cleaned.head())  # Verify that the new features were added

    # Report the number of examples
    print(f"Number of examples in the processed dataset: {len(df_cleaned)}")

    # Save processed data to CSV
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    output_path = os.path.join(data_dir, output_filename)  # Save in the 'data' folder
    df_cleaned.to_csv(output_path, index=False)
    print(f"Processed data saved to {output_path}")

