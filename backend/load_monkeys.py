import mailbox
import pandas as pd
import re
from bs4 import BeautifulSoup
import os

def extract_urls(text):
    url_regex = r'https?://[^\s"<>]+'
    return re.findall(url_regex, text or "")

def extract_body(msg):
    if msg.is_multipart():
        parts = []
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == 'text/plain' or ctype == 'text/html':
                try:
                    content = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
                    parts.append(content)
                except:
                    continue
        return '\n'.join(parts)
    else:
        try:
            return msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='replace')
        except:
            return ""

def clean_html(text):
    soup = BeautifulSoup(text or "", "html.parser")
    return soup.get_text(separator="\n")

def has_attachments(msg):
    for part in msg.walk():
        if part.get_content_disposition() == 'attachment':
            return True
    return False

def process_mbox(mbox_path, data_dir):
    # Ensure the data directory exists
    os.makedirs(data_dir, exist_ok=True)

    # Path for output CSV
    csv_output_path = os.path.join(data_dir, "phishing3.csv")

    mbox = mailbox.mbox(mbox_path)
    rows = []

    for message in mbox:
        sender = message.get('From', '')
        subject = message.get('Subject', '')
        date = message.get('Date', '')
        reply_to = message.get('Reply-To', '')
        message_id = message.get('Message-ID', '')
        content_type = message.get_content_type()
        attachment_flag = has_attachments(message)

        raw_body = extract_body(message)
        clean_body = clean_html(raw_body)
        urls = extract_urls(raw_body)

        row = {
            'sender': sender,
            'subject': subject,
            'date': date,
            'reply_to': reply_to,
            'message_id': message_id,
            'content_type': content_type,
            'has_attachment': attachment_flag,
            'body': clean_body,
            'urls': ';'.join(urls),
            'label': 1  # All messages are phishing in this dataset
        }

        rows.append(row)

    df = pd.DataFrame(rows)

    # Double-check the label distribution after processing
    label_counts_after = df['label'].value_counts()
    print("Label distribution after processing:")
    for label, count in label_counts_after.items():
        label_name = "Phishing" if label == 1 else "Ham"
        print(f"{label_name} ({label}): {count}")

    df.to_csv(csv_output_path, index=False)
    print(f"Saved {len(df)} emails to {csv_output_path}")

if __name__ == "__main__":
    # Define the data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")

    # Path to the MBOX file
    mbox_path = os.path.join(data_dir, "phishing3.mbox")

    # Process the MBOX file and save the CSV
    process_mbox(mbox_path, data_dir)
