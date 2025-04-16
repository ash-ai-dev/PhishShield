import os
import re
import pandas as pd
import kagglehub
from dotenv import load_dotenv

def process_and_save_dataset(dataset_name, output_filename="ham_emails.csv"):  
    # Load Kaggle API keys from kaggle.env
    load_dotenv(dotenv_path="kaggle.env")
    KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
    KAGGLE_KEY = os.getenv("KAGGLE_KEY")

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

    csv_path = os.path.join(dataset_path, csv_files[0])

    # Load and process data
    df = pd.read_csv(csv_path)

    # Check the first few rows to inspect the data
    print(df.head()) 

    df = df[df['label'].notna()]

    if 'label' not in df.columns:
        print("Error: 'label' column not found.")
        return

    # Filter for 'Ham' examples only
    df = df[df['label'] == 0] 

    # Double-check the distribution after filtering
    label_counts_after = df['label'].value_counts()
    print("Label distribution after filtering:")
    for label, count in label_counts_after.items():
        label_name = "Ham" if label == 0 else "Spam"
        print(f"{label_name} ({label}): {count}")

    if df.empty:
        print("No 'Ham' examples found.")
        return

    features_list = df.apply(lambda row: extract_features_from_content(row['subject'], row['message']), axis=1)
    features_df = pd.json_normalize(features_list)

    # Combine original dataset with the extracted features
    full_df = pd.concat([df, features_df], axis=1)

    # Remove duplicates based on 'subject' and 'message' columns
    df_cleaned = full_df.drop_duplicates(subset=["subject", "message"], keep="first")

    # Double-check the number of rows after removing duplicates
    print(f"Number of rows after dropping duplicates: {len(df_cleaned)}")

    df_cleaned = df_cleaned.drop(index=0)

    column_order = ['sender', 'subject', 'date', 'reply_to', 'message_id', 'content_type', 'has_attachment', 'body', 'urls', 'label']
    df_cleaned = df_cleaned[column_order]

    print(df_cleaned.head())

    print(f"Number of examples in the processed dataset: {len(df_cleaned)}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    output_path = os.path.join(data_dir, output_filename)  # Save in the 'data' folder
    df_cleaned.to_csv(output_path, index=False)
    print(f"Processed data saved to {output_path}")

# Feature extraction functions 
def extract_features_from_content(subject, body):
    features = {
        'sender': extract_sender(body),
        'subject': subject,
        'date': extract_date(body),
        'reply_to': extract_reply_to(body),
        'message_id': extract_message_id(body),
        'content_type': 'text/plain',
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
