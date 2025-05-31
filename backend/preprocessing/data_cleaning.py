import pandas as pd
import os
import re

input_file = '../data/preprocessed/all_emails_labeled.csv'
output_file = '../data/preprocessed/all_emails_cleaned.csv'

def report_drop(df_before, df_after, step_desc):
    phishing_dropped = df_before[df_before['Label'] == 1].shape[0] - df_after[df_after['Label'] == 1].shape[0]
    total_dropped = len(df_before) - len(df_after)
    print(f"🔧 {step_desc}: Dropped {total_dropped} rows, including {phishing_dropped} phishing emails (Label 1).")

# Load the labeled data
try:
    df = pd.read_csv(input_file)

    print(f"📥 Loaded {len(df)} total rows from input.")

    # --- 1. Drop rows with missing values in key text fields ---
    before = df.copy()
    df = df.dropna(subset=['Subject', 'Body'])
    report_drop(before, df, "Drop rows with missing Subject or Body")

    # --- 2. Drop unnecessary metadata columns like 'Date' ---
    if 'Date' in df.columns:
        df.drop(columns=['Date'], inplace=True)
        print("🗑️ Dropped 'Date' column.")

    # --- 3. Remove duplicate rows based on From, To, Subject, and Body ---
    before = df.copy()
    df = df.drop_duplicates(subset=['From', 'To', 'Subject', 'Body'])
    report_drop(before, df, "Remove duplicate emails")

    # --- 4. Remove rows where key fields are just empty strings or whitespace ---
    before = df.copy()
    df = df[~df[['Subject', 'Body']].applymap(lambda x: isinstance(x, str) and x.strip() == '').any(axis=1)]
    report_drop(before, df, "Remove empty Subject or Body fields")

    # --- 5. Normalize text fields: lowercase and strip excessive whitespace ---
    def clean_text(text):
        text = text.lower()
        text = ' '.join(text.split())
        return text

    for col in ['Subject', 'Body']:
        df[col] = df[col].astype(str).apply(clean_text)
    print("🧼 Normalized Subject and Body text.")

    # --- 6. Remove rows where the email body is too short to be useful ---
    before = df.copy()
    df = df[df['Body'].str.len() > 10]
    report_drop(before, df, "Remove emails with very short Body text")

    # --- 7. Ensure 'From' and 'To' are valid email addresses ---
    """
    before = df.copy()
    email_pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")
    df = df[
        df['From'].apply(lambda x: bool(email_pattern.match(str(x)))) &
        df['To'].apply(lambda x: bool(email_pattern.match(str(x))))
    ]
    report_drop(before, df, "Remove rows with invalid 'From' or 'To' emails")
    """

    # --- 8. Reset index after all cleaning steps ---
    df.reset_index(drop=True, inplace=True)

    # --- 9. Save the cleaned DataFrame ---
    df.to_csv(output_file, index=False)
    print(f"\n✅ Cleaned data saved to {output_file} with {len(df)} rows (Phishing emails remaining: {df[df['label'] == 1].shape[0]}).")

except FileNotFoundError:
    print(f"❌ Input file not found: {input_file}")
except Exception as e:
    print(f"⚠️ An error occurred: {e}")
