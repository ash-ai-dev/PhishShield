import csv
import os

# Input CSV (Lingspam with subject, message, label)
input_csv = '../data/raw_kaggle/messages.csv'
output_dir = '../data/extracted'
os.makedirs(output_dir, exist_ok=True)
output_csv = os.path.join(output_dir, 'parsed_lingspam_ham.csv')

# List to hold extracted HAM messages
ham_data = []

# Read and filter only label 0 (HAM)
with open(input_csv, 'r', encoding='utf-8', errors='replace') as f:
    reader = csv.DictReader(f)
    
    for i, row in enumerate(reader):
        if row.get('label') == '0':
            subject = row.get('subject', '').strip()
            message = row.get('message', '').strip()
            ham_data.append({'Subject': subject, 'Body': message})

        if i % 500 == 0:
            print(f"Checked {i} rows")

# Write output CSV
with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
    fieldnames = ['Subject', 'Body']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(ham_data)

print(f"Done. Extracted {len(ham_data)} HAM emails to {output_csv}")
