import os
import pandas as pd
from bs4 import BeautifulSoup

def preprocess_phishing_dataset(dataset_path, output_filename="phishing_emails_cleaned.csv"):
    try:
        # Ensure the dataset directory exists
        if not os.path.isdir(dataset_path):
            raise FileNotFoundError(f"The directory '{dataset_path}' does not exist!")

        # Load all CSV files in the folder
        csv_files = [f for f in os.listdir(dataset_path) if f.endswith(".csv")]

        if not csv_files:
            raise FileNotFoundError("No CSV files found in the dataset directory!")

        print(f"Found {len(csv_files)} CSV files. Merging them now...")

        # Read and merge datasets
        dfs = []
        for file in csv_files:
            file_path = os.path.join(dataset_path, file)
            print(f"Loading {file}...")
            df = pd.read_csv(file_path)
            dfs.append(df)

        # Combine all DataFrames into one
        merged_df = pd.concat(dfs, ignore_index=True)
        print("Datasets merged successfully!")

        # Output dataset size and label counts
        num_examples = len(merged_df)
        print(f"\nTotal number of examples: {num_examples}")

        if "label" in merged_df.columns:
            label_counts = merged_df["label"].value_counts()
            print(f"\nLabel distribution:\n{label_counts}")
        else:
            print("Warning: 'label' column not found. Cannot display label distribution.")

        # Check for missing values
        print("\nChecking for missing values...")
        missing_values = merged_df.isnull().sum()
        print(missing_values[missing_values > 0])  # Show only columns with missing data

        # Fill missing values with NaN (or a placeholder like "unknown" or empty string "")
        for column in merged_df.columns:
            if merged_df[column].dtype == 'object': 
                merged_df[column].fillna("unknown", inplace=True)
            else:  
                merged_df[column].fillna(merged_df[column].mean(), inplace=True)

        # Drop duplicate rows (if any)
        print("\nRemoving duplicate rows...")
        merged_df.drop_duplicates(inplace=True)

        # Standardize column names (optional)
        merged_df.columns = merged_df.columns.str.lower().str.replace(" ", "_")

        # Basic text preprocessing (cleaning emails)
        print("\nCleaning email content...")
        
        def remove_html_tags(text):
            """Remove HTML tags from the text."""
            return BeautifulSoup(text, "html.parser").get_text()

        if "body" in merged_df.columns:
            merged_df["body"] = merged_df["body"].astype(str)  # Ensure column is string
            merged_df["body"] = merged_df["body"].apply(remove_html_tags)  # Remove HTML tags
            merged_df["body"] = merged_df["body"].str.replace(r"\s+", " ", regex=True)  # Remove excessive whitespace
            merged_df["body"] = merged_df["body"].str.replace(r"[^A-Za-z0-9\s]", "", regex=True)  # Remove alphabet/number characters
            merged_df["body"] = merged_df["body"].str.lower()  # Convert to lowercase
            merged_df["body"] = merged_df["body"].str.strip()  # Remove leading/trailing spaces
        else:
            print("Warning: 'body' column not found. Skipping text cleaning.")

        # Check if output file already exists
        cleaned_csv_path = os.path.join(dataset_path, output_filename)
        
        if os.path.exists(cleaned_csv_path):
            # Read the existing cleaned CSV to check for duplicates
            print(f"Checking for duplicates with the existing cleaned file...")
            existing_df = pd.read_csv(cleaned_csv_path)
            
            # Merge the new data and existing data and drop duplicates
            merged_df = pd.concat([existing_df, merged_df], ignore_index=True).drop_duplicates()

            # Check if the resulting data is unchanged
            if len(merged_df) == len(existing_df):
                print("No new data to add.")
                return cleaned_csv_path  # No new data added, return the existing file path
            
        # Save preprocessed dataset
        merged_df.to_csv(cleaned_csv_path, index=False)
        print(f"\nPreprocessed dataset saved at: {cleaned_csv_path}")

        # Show sample data after preprocessing
        print("\nSample Data after Preprocessing:\n", merged_df.head())

        return cleaned_csv_path

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None
    except FileExistsError as e:
        print(f"Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    dataset_path = data_dir  # Path to the original CSV files

    if os.path.isdir(dataset_path):
        cleaned_csv_path = preprocess_phishing_dataset(dataset_path)

        if cleaned_csv_path:
            print(f"Preprocessed data saved to: {cleaned_csv_path}")
        else:
            print("Preprocessing failed.")
    else:
        print(f"Error: The 'data' directory does not exist at {dataset_path}.")
