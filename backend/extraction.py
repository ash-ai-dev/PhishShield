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
    "congratulations", "lottery", "credit card", "security alert", "confirm", "verify your account", 
    "update your information", "click here to login", "urgent action required", "confirm your password", 
    "your account has been compromised", "reset your password", "you have won", "claim your prize", 
    "security alert", "banking notification", "free gift", "limited offer", "download attachment"
]

# Common free email providers
FREE_EMAIL_PROVIDERS = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"]

# Suspicious domain extensions
SUSPICIOUS_DOMAINS = [".ru", ".cn", ".xyz", ".top", ".biz", ".tk"]

def is_fuzzy_match(text, patterns, threshold=80):
    for pattern in patterns:
        if fuzz.partial_ratio(pattern, text) > threshold:
            return True
    return False


def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) 
    except Exception:
        return False

def extract_features(email):
    body = str(email.get("body", ""))  # Ensure fields are strings
    subject = str(email.get("subject", "")) 
    sender_email = str(email.get("sender", "")) 
    features = {}

    # Basic Text Features
    features["num_words"] = len(body.split()) if body else 0
    features["num_chars"] = len(body) if body else 0
    features["num_uppercase"] = sum(1 for char in body if char.isupper())
    features["num_special_chars"] = sum(1 for char in body if char in "!@#$%^&*()")
    features["subject_length"] = len(subject) if subject else 0

    # URL-Based Features
    urls = re.findall(r'(https?://\S+)', body)
    features["num_urls"] = len(urls)
    features["num_shortened_urls"] = sum(1 for url in urls if "bit.ly" in url or "tinyurl.com" in url)
    features["url_avg_length"] = np.mean([len(url) for url in urls]) if urls else 0
    features["url_contains_numbers"] = sum(any(char.isdigit() for char in url) for url in urls)

    # Keyword-Based Features
    features["num_suspicious_keywords"] = sum(1 for word in SUSPICIOUS_KEYWORDS if word in body.lower())
    features["suspicious_word_ratio"] = features["num_suspicious_keywords"] / features["num_words"] if features["num_words"] > 0 else 0

    # Subject Features
    features["subject_contains_suspicious_word"] = any(word in subject.lower() for word in SUSPICIOUS_KEYWORDS)

    
    return features

# Example email for testing
email_sample = {
    "sender": "Young Esposito <Young@iworld.de>",
    "receiver": "user4@gvc.ceas-challenge.cc",
    "date": "Tue, 05 Aug 2008 16:31:02 -0700",
    "subject": "Never agree to be a loser",
    "body": "Buck up, your troubles caused by small dimension will soon be over! Become a lover no woman will be able to resist! http://whitedone.com/ come. Even as Nazi tanks were rolling down the streets...",
}

# Extract features
features = extract_features(email_sample)
print(features)
