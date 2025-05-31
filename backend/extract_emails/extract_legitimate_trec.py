import csv
import re
import os
import sys
from html import unescape

csv.field_size_limit(sys.maxsize)

input_csv = '../data/raw_kaggle/email_origin.csv'
output_dir = '../data/extracted'
os.makedirs(output_dir, exist_ok=True)
output_csv = os.path.join(output_dir, 'parsed_trec_emails.csv')

# --- Helper function to extract From, To, Subject, and Body ---
def extract_fields(email_text):
    # Normalize line endings and remove null characters
    email_text = email_text.replace('\x00', '').replace('\r\n', '\n')

    # Extract From, To, Subject
    from_match = re.search(r'^From:\s*(.*)', email_text, re.MULTILINE)
    to_match = re.search(r'^To:\s*(.*)', email_text, re.MULTILINE)
    subject_match = re.search(r'^Subject:\s*(.*)', email_text, re.MULTILINE)

    from_ = from_match.group(1).strip() if from_match else ''
    to = to_match.group(1).strip() if to_match else ''
    subject = subject_match.group(1).strip() if subject_match else ''

    # Extract Body
    body = ''
    if 'Content-Type:' in email_text:
        # Try to find HTML or plain text
        body_match = re.search(
            r'(?:Content-Type:\s*text/html.*?\n\n)(.*?)(?:--\S+--|\Z)',
            email_text, re.DOTALL | re.IGNORECASE)
        if not body_match:
            body_match = re.search(
                r'(?:Content-Type:\s*text/plain.*?\n\n)(.*?)(?:--\S+--|\Z)',
                email_text, re.DOTALL | re.IGNORECASE)
        if body_match:
            body = body_match.group(1).strip()
    else:
        # Fallback: get everything after header section
        body_start = email_text.find('\n\n')
        if body_start != -1:
            body = email_text[body_start:].strip()

    # Clean HTML tags
    body = re.sub(r'<[^>]+>', '', body)
    body = unescape(body)

    return {
        'From': from_,
        'To': to,
        'Subject': subject,
        'Body': body
    }

# --- Main Extraction Loop ---
extracted_data = []
with open(input_csv, 'r', encoding='utf-8', errors='replace') as f:
    cleaned_lines = (line.replace('\x00', '') for line in f.readlines())
    reader = csv.reader(cleaned_lines)

    for i, row in enumerate(reader):
        if len(row) < 2:
            continue

        label = row[0].strip()
        if label != '0':  # Only process HAM emails
            continue

        email_text = row[1]
        fields = extract_fields(email_text)
        extracted_data.append(fields)

        if i % 5000 == 0:
            print(f"Processed {i} rows")

# --- Write Results ---
with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
    fieldnames = ['From', 'To', 'Subject', 'Body']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(extracted_data)

print(f"Done. Extracted {len(extracted_data)} emails to {output_csv}")
