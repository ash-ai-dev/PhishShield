import mailbox
import pandas as pd
import re
from bs4 import BeautifulSoup
import os

def extract_urls(text):
    """Extracts all URLs from a block of text."""
    url_regex = r'https?://[^\s"<>]+'
    return re.findall(url_regex, text or "")

def extract_body(msg):
    """Extracts the email body from plain text or HTML parts."""
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
    """Strips HTML tags and extracts visible text."""
    soup = BeautifulSoup(text or "", "html.parser")
    return soup.get_text(separator="\n")

def has_attachments(msg):
    """Checks if the email contains any attachments."""
    for part in msg.walk():
        if part.get_content_disposition() == 'attachment':
            return True
    return False

def process_mbox(mbox_path, data_dir):
    """Parses the MBOX and writes structured CSV with extracted features."""
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
    df.to_csv(csv_output_path, index=False)
    print(f"✅ Saved {len(df)} emails to {csv_output_path}")

# Example usage:
if __name__ == "__main__":
    # Define the data directory to save the CSV and read the MBOX
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")

    # Path to the MBOX file inside the data directory
    mbox_path = os.path.join(data_dir, "phishing3.mbox")

    # Process the MBOX file and save the CSV to the data directory
    process_mbox(mbox_path, data_dir)
