import os
import pandas as pd
import numpy as np

# Path to CSV files
data_folder = "data/preprocessed"

# Ensure folder exists
if not os.path.exists(data_folder):
    print(f"❌ Data folder not found: {data_folder}")
    exit()

# List all CSV files in the folder
csv_files = [f for f in os.listdir(data_folder) if f.endswith(".csv")]

if not csv_files:
    print("❗ No CSV files found in the data directory.")
    exit()

for csv_file in csv_files:
    file_path = os.path.join(data_folder, csv_file)
    print("\n--------------------------------------------------------\n")
    print(f"\n📂 Analyzing file: {csv_file}")

    try:
        df = pd.read_csv(file_path)

        # Basic overview
        print("\n🔍 Basic Info:")
        print(f"Total rows (emails): {len(df)}")
        print(df.info())

        # Descriptive statistics
        print("\n📊 Description:")
        print(df.describe(include="all"))

        # Unique senders and recipients
        if "From" in df.columns:
            print(f"\n👤 Unique senders: {df['From'].nunique()}")
        if "To" in df.columns:
            print(f"📩 Unique recipients: {df['To'].nunique()}")

        # Missing data summary
        print("\n🚨 Missing Fields Count:")
        print(df.isnull().sum())

        # Label distribution
        if "Label" in df.columns:
            print("\n🏷️ Label Distribution:")
            print(df['Label'].value_counts())
            print("\n🔢 Label Distribution (%):")
            print(df['Label'].value_counts(normalize=True).apply(lambda x: f"{x:.2%}"))

        # Preview examples
        print("\n📝 Sample Subjects and Bodies:")
        if "Subject" in df.columns:
            print("Subjects:\n", df["Subject"].dropna().head(3).to_string(index=False))
        if "Body" in df.columns:
            print("Bodies:\n", df["Body"].dropna().str.slice(0, 100).head(2).to_string(index=False))

    except Exception as e:
        print(f"❌ Failed to analyze {csv_file}: {e}")
