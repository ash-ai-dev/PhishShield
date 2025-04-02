import os
import re
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from collections import Counter
import base64
from urllib.parse import urlparse

# Expanded list of suspicious keywords
SUSPICIOUS_KEYWORDS = [
    "urgent", "password", "verify", "bank", "account", "login", "click", "update",
    "free", "win", "prize", "guarantee", "limited offer", "unsubscribe", "claim now",
    "congratulations", "lottery", "credit card", "security alert", "confirm",     "verify your account", "update your information", "click here to login",
    "urgent action required", "confirm your password", "your account has been compromised",
    "reset your password", "you have won", "claim your prize", "security alert",
    "banking notification", "free gift", "limited offer", "download attachment"
]

# Common free email providers (spam often spoofs these)
FREE_EMAIL_PROVIDERS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"]

# Suspicious domain extensions (often linked to spam)
SUSPICIOUS_DOMAINS = [".ru", ".cn", ".xyz", ".top", ".biz", ".tk"]

def is_fuzzy_match(text, patterns, threshold=80):
    """
    Checks if any phrase in the text is a fuzzy match to the given patterns.
    """
    for pattern in patterns:
        if fuzz.partial_ratio(pattern, text) > threshold:
            return True
    return False


def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc)  # Ensure it has a valid domain
    except Exception:
        return False

def extract_features(email):
    """
    Extracts multiple features from an email body and metadata.
    :param email: Dictionary containing sender, receiver, subject, body.
    :return: Dictionary of extracted features.
    """
    body = str(email.get("body", ""))  # Ensure body is a string
    subject = str(email.get("subject", ""))  # Ensure subject is a string
    sender_email = str(email.get("sender", ""))  # Ensure sender is a string
    features = {}

    # ✅ 1. Basic Text Features
    features["num_words"] = len(body.split())
    features["num_chars"] = len(body)
    features["num_uppercase"] = sum(1 for char in body if char.isupper())
    features["num_special_chars"] = sum(1 for char in body if char in "!@#$%^&*()")
    features["subject_length"] = len(subject) 

    # ✅ 2. URL-Based Features
    urls = re.findall(r'(https?://\S+)', body)
    features["num_urls"] = len(urls)
    features["num_shortened_urls"] = sum(1 for url in urls if "bit.ly" in url or "tinyurl.com" in url)
    features["url_avg_length"] = np.mean([len(url) for url in urls]) if urls else 0
    features["url_contains_numbers"] = sum(any(char.isdigit() for char in url) for url in urls)

    # ✅ 3. Suspicious Domain Features
    extracted_domains = [urlparse(url).netloc for url in urls if is_valid_url(url)]
    features["suspicious_domain_count"] = sum(1 for domain in extracted_domains if any(ext in domain for ext in SUSPICIOUS_DOMAINS))

    # ✅ 4. Detecting Base64/Hex-Encoded URLs
    def is_encoded(text):
        try:
            base64.b64decode(text)
            return True
        except Exception:
            return False
    features["num_encoded_urls"] = sum(1 for url in urls if is_encoded(url))

    # ✅ 5. Keyword-Based Features
    features["num_suspicious_keywords"] = sum(1 for word in SUSPICIOUS_KEYWORDS if word in body.lower())
    features["suspicious_word_ratio"] = features["num_suspicious_keywords"] / features["num_words"] if features["num_words"] > 0 else 0

    # ✅ 6. Subject Features
    features["subject_length"] = len(subject)
    features["subject_contains_suspicious_word"] = any(word in subject.lower() for word in SUSPICIOUS_KEYWORDS)

    # ✅ 7. Excessive Punctuation & HTML Presence
    features["num_exclamation"] = body.count("!")
    features["num_question_marks"] = body.count("?")
    features["contains_html"] = int(bool(re.search(r'<[^>]+>', body)))  # Detects HTML tags

    # ✅ 8. Email Header-Based Features
    sender_domain = sender_email.split("@")[-1] if "@" in sender_email else ""
    features["sender_is_free_email"] = int(sender_domain in FREE_EMAIL_PROVIDERS)
    features["sender_email_length"] = len(sender_email)
    features["sender_has_random_numbers"] = int(bool(re.search(r'\d', sender_email)))  # Common in spam addresses

    """"
    ### ✅ 9. Keyword-Based Features (Fuzzy Matching)
    features["num_suspicious_phrases"] = sum(is_fuzzy_match(body, [phrase]) for phrase in SUSPICIOUS_KEYWORDS)
    features["subject_contains_suspicious_phrases"] = int(is_fuzzy_match(subject, SUSPICIOUS_KEYWORDS))

    # ✅ 10. Repetitive Words (Spam Emails Often Repeat Words)
    words = body.split()
    word_counts = Counter(words)
    most_common_word, most_common_freq = word_counts.most_common(1)[0] if words else ("", 0)
    features["most_common_word_freq"] = most_common_freq / len(words) if words else 0
    """
    return features

# Example Email Data
email_sample = {
    "sender": "Young Esposito <Young@iworld.de>",
    "receiver": "user4@gvc.ceas-challenge.cc",
    "date": "Tue, 05 Aug 2008 16:31:02 -0700",
    "subject": "Never agree to be a loser",
    "body": "Buck up, your troubles caused by small dimension will soon be over! Become a lover no woman will be able to resist! http://whitedone.com/ come. Even as Nazi tanks were rolling down the streets...",
}

# Extract Features
features = extract_features(email_sample)
print(features)
