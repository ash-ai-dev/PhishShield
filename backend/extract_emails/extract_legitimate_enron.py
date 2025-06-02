import csv
import re
import os
import sys

csv.field_size_limit(2**31 - 1)

output_dir = '../data/extracted'
output_csv = os.path.join(output_dir, 'parsed_enron_emails.csv')

def extract_fields(email_text):
    from_match = re.search(r'^From: (.+)', email_text, re.MULTILINE)
    to_match = re.search(r'^To: (.+)', email_text, re.MULTILINE)
    subject_match = re.search(r'^Subject: (.*)', email_text, re.MULTILINE)
    
    # The body is everything after the first empty line (headers end)
    body = email_text.split('\n\n', 1)[1] if '\n\n' in email_text else ''

    return {
        'From': from_match.group(1).strip() if from_match else '',
        'To': to_match.group(1).strip() if to_match else '',
        'Subject': subject_match.group(1).strip() if subject_match else '',
        'Body': body.strip()
    }

# Read the CSV file
with open('../data/raw_kaggle/emails.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    extracted_data = []

    for i, row in enumerate(reader):
        if i >= 110000:
            break
        message = row['message']
        fields = extract_fields(message)
        extracted_data.append(fields)

        if i % 5000 == 0:
            print(f"Processed {i} emails")

# Save to new CSV file
with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
    fieldnames = ['From', 'To', 'Subject', 'Body']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(extracted_data)
