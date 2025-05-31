import os
import csv
import mailbox

# Directory containing mbox files
mbox_dir = '../mbox_files'
output_dir = '../data/extracted'
output_csv = os.path.join(output_dir, 'extracted_phishing.csv')

# Fields to extract
fields = ['From', 'To', 'Subject', 'Date', 'Body']

def extract_body(message):
    """Extract plain text body from the email."""
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == 'text/plain':
                try:
                    return part.get_payload(decode=True).decode(part.get_content_charset('utf-8'), errors='replace')
                except:
                    return ""
    else:
        try:
            return message.get_payload(decode=True).decode(message.get_content_charset('utf-8'), errors='replace')
        except:
            return ""
    return ""


def parse_mbox_file(filepath):
    emails = []
    try:
        mbox = mailbox.mbox(filepath, factory=None, create=False)
        for key in mbox.iterkeys():
            try:
                message = mbox.get_message(key)
                email = {
                    'From': message.get('From', ''),
                    'To': message.get('To', ''),
                    'Subject': message.get('Subject', ''),
                    'Date': message.get('Date', ''),
                    'Body': extract_body(message)
                }
                emails.append(email)
            except Exception as e:
                print(f"Skipping a message due to error: {e}")
    except Exception as e:
        print(f"Failed to parse mbox file {filepath}: {e}")
    return emails


def main():
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    all_emails = []

    for filename in os.listdir(mbox_dir):
        if filename.endswith('.mbox'):
            filepath = os.path.join(mbox_dir, filename)
            print(f"Processing {filepath}")
            emails = parse_mbox_file(filepath)
            all_emails.extend(emails)

    # Write to CSV inside the output directory
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_emails)

    print(f"\n✅ Extraction complete. Data written to: {output_csv}")

if __name__ == '__main__':
    main()
