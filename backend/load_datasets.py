import os
import pandas as pd
import kagglehub
from dotenv import load_dotenv

def load_and_get_dataset_path(dataset_name, data_dir):
    """Downloads dataset if needed and returns the path."""
    os.makedirs(data_dir, exist_ok=True)

    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    if not csv_files:
        try:
            print("Downloading dataset from Kaggle...")
            path = kagglehub.dataset_download(dataset_name)
            if path:
                print(f"Dataset downloaded to: {path}")
                return path
            else:
                print("Dataset download failed.")
                return None  # Indicate download failure
        except kagglehub.exceptions.KaggleApiHTTPError as e:
            print(f"Error downloading dataset: {e}")
            return None  # Indicate download failure
    else:
        return data_dir # dataset already there.

if __name__ == "__main__":
    # Load Kaggle API keys from kaggle.env
    load_dotenv(dotenv_path="kaggle.env")
    KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME")
    KAGGLE_KEY = os.getenv("KAGGLE_KEY")

    # Check if credentials are loaded
    if not KAGGLE_USERNAME or not KAGGLE_KEY:
        print("Kaggle API credentials not found. Please create a kaggle.env file with KAGGLE_USERNAME and KAGGLE_KEY.")
        exit(1)

    # Kaggle dataset details
    dataset_name = "naserabdullahalam/phishing-email-dataset"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")

    dataset_path = load_and_get_dataset_path(dataset_name, data_dir)

    if dataset_path:
        # Construct the CSV path
        csv_files = [f for f in os.listdir(dataset_path) if f.endswith('.csv')]
        if csv_files:
            csv_path = os.path.join(dataset_path, csv_files[0])
            try:
                df = pd.read_csv(csv_path)
                print(df.head())
                print("\nDataset Info:\n", df.info())
                # You can now pass the dataset_path to other functions or scripts
                # e.g., feature_extraction(df, dataset_path)
            except FileNotFoundError:
                print(f"Error: CSV file not found at {csv_path}")
                exit(1)
        else:
            print("Error: No CSV file found in downloaded dataset.")
            exit(1)
    else:
        print("Failed to load dataset.")
        exit(1)