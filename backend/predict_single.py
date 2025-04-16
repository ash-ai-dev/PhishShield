import joblib
import pandas as pd
from extraction import extract_features

model = joblib.load("data/lr_model.pkl")
scaler = joblib.load("data/scaler.pkl")

feature_columns = [
    'num_words', 'num_chars', 'num_uppercase', 'num_special_chars',
    'num_urls', 'num_shortened_urls', 'url_avg_length', 'url_contains_numbers',
    'num_suspicious_keywords', 'suspicious_word_ratio', 'subject_contains_suspicious_word'
]

def predict_email(email_dict):
    row = pd.Series(email_dict)
    features = extract_features(row)
    features_df = pd.DataFrame([features]) 

    features_scaled = scaler.transform(features_df[feature_columns])

    prediction = model.predict(features_scaled)[0]
    label = "Phishing" if prediction == 1 else "Ham"
    return label

# Example
if __name__ == "__main__":
    email = {
        "sender": "security@bank.com",
        "subject": "Verify your account now",
        "date": "Tue, 2 Apr 2024 08:45:00 +0000",
        "reply_to": "noreply@bank.com",
        "message_id": "<msg123@bank.com>",
        "content_type": "text/plain",
        "has_attachment": False,
        "body": "Click here to verify your account urgently: http://bit.ly/phishlink",
        "urls": ["http://bit.ly/phishlink"]
    }

    result = predict_email(email)
    print("Prediction:", result)
