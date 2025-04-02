import os
import pandas as pd

def preprocess_phishing_dataset(dataset_path, output_filename="phishing_emails_cleaned.csv"):
    """
    Preprocesses the phishing email dataset.

    Args:
        dataset_path (str): Path to the directory containing the original CSV files.
        output_filename (str, optional): Name of the output CSV file. Defaults to "phishing_emails_cleaned.csv".

    Returns:
        str: Path to the preprocessed dataset CSV file, or None if an error occurred.
    """
    try:
        # Step 1: Load all CSV files in the folder
        csv_files = [f for f in os.listdir(dataset_path) if f.endswith(".csv")]

        if not csv_files:
            raise FileNotFoundError("No CSV files found in the dataset directory!")

        print(f"Found {len(csv_files)} CSV files. Merging them now...")

        # Step 2: Read and merge datasets
        dfs = []
        for file in csv_files:
            file_path = os.path.join(dataset_path, file)
            print(f"Loading {file}...")
            df = pd.read_csv(file_path)
            dfs.append(df)

        # Combine all DataFrames into one
        merged_df = pd.concat(dfs, ignore_index=True)
        print("Datasets merged successfully!")

        # Step 3: Check for missing values
        print("\nChecking for missing values...")
        missing_values = merged_df.isnull().sum()
        print(missing_values[missing_values > 0])  # Show only columns with missing data

        # Step 4: Drop duplicate rows (if any)
        print("\nRemoving duplicate rows...")
        merged_df.drop_duplicates(inplace=True)

        # Step 5: Standardize column names (optional)
        merged_df.columns = merged_df.columns.str.lower().str.replace(" ", "_")

        # Step 6: Basic text preprocessing (cleaning emails)
        print("\nCleaning email content...")
        if "body" in merged_df.columns:
            merged_df["body"] = merged_df["body"].astype(str)  # Ensure column is string
            merged_df["body"] = merged_df["body"].str.replace(r"\s+", " ", regex=True)  # Remove excessive whitespace
        else:
            print("Warning: 'body' column not found. Skipping text cleaning.")

        # Step 7: Save preprocessed dataset
        cleaned_csv_path = os.path.join(dataset_path, output_filename)
        merged_df.to_csv(cleaned_csv_path, index=False)
        print(f"\nPreprocessed dataset saved at: {cleaned_csv_path}")

        # Show sample data after preprocessing
        print("\nSample Data after Preprocessing:\n", merged_df.head())

        return cleaned_csv_path

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# example of how to call the function.
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    dataset_path = data_dir # the path to the original csv files.
    cleaned_csv_path = preprocess_phishing_dataset(dataset_path)

    if cleaned_csv_path:
        print(f"Preprocessed data saved to: {cleaned_csv_path}")
    else:
        print("Preprocessing failed.")