import os
import pandas as pd

input_dir = '../data/extracted'
output_file = '../data/preprocessed/all_emails_labeled.csv'

all_data = []

# Go through every CSV file in the extracted folder
for filename in os.listdir(input_dir):
    if filename.endswith('.csv'):
        filepath = os.path.join(input_dir, filename)

        # Determine label based on filename
        label = 1 if 'phishing' in filename.lower() else 0

        # Read the CSV and add label
        try:
            df = pd.read_csv(filepath)
            df['Label'] = label
            all_data.append(df)
            print(f"Loaded {filename} with label {label}")
        except Exception as e:
            print(f"Could not process {filename}: {e}")

# Combine all data into a single DataFrame
if all_data:
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df.to_csv(output_file, index=False)
    print(f"\nDone. Saved {len(combined_df)} labeled emails to: {output_file}")
else:
    print("No data was loaded. Please check the input directory and filenames.")
