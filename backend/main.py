import os
import openai
import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi import HTTPException
import requests
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from extraction import extract_features
from fastapi.testclient import TestClient

load_dotenv(dotenv_path="openAI.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load API key from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


# Load model and scaler
model = joblib.load("data/lr_model.pkl")
scaler = joblib.load("data/scaler.pkl")

feature_columns = [
    'num_words', 'num_chars', 'num_uppercase', 'num_special_chars',
    'num_urls', 'num_shortened_urls', 'url_avg_length', 'url_contains_numbers',
    'num_suspicious_keywords', 'suspicious_word_ratio', 'subject_contains_suspicious_word'
]

app = FastAPI()

client = TestClient(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmailData(BaseModel):
    email_body: str
    sender: str
    subject: str
    received_time: str

# Function to predict phishing status
def predict_email(email_dict):
    row = pd.Series(email_dict)
    features = extract_features(row)
    features_df = pd.DataFrame([features])

    features_scaled = scaler.transform(features_df[feature_columns])

    prediction = model.predict(features_scaled)[0]
    label = "Phishing" if prediction == 1 else "Ham"
    return label

@app.post("/email")
async def receive_email(email_data: EmailData):
    print(f"Received email data: {email_data}")

    email_dict = {
        "sender": email_data.sender,
        "subject": email_data.subject,
        "date": email_data.received_time,
        "reply_to": "", 
        "message_id": "", 
        "content_type": "text/plain", 
        "has_attachment": False, 
        "body": email_data.email_body,
        "urls": [] 
    }

    # Predict phishing status
    prediction = predict_email(email_dict)

    # Log prediction to the terminal
    print("Prediction result:", prediction)

    # If phishing, forward the email content to /explain
    if prediction == "Phishing":
        print("Test")
        explain_payload = {
            "subject": email_data.subject,
            "body": email_data.email_body,
            "sender": email_data.sender
        }

        try:
            explain_response = client.post("/explain", json=explain_payload)
            if explain_response.status_code == 200:
                explanation = explain_response.json().get("explanation", "")
        except Exception as e:
            explanation = "Failed to get explanation after multiple attempts."
    else:
        explanation = "This email does not appear to be phishing."

    return JSONResponse(content={
        "status": "success",
        "prediction": prediction,
        "explanation": explanation
    })

@app.post("/explain")
async def explain_phishing(payload: dict):
    print("🔍 Received request for /explain")

    subject = payload.get("subject", "")
    body = payload.get("body", "")
    sender = payload.get("sender", "")

    prompt = f"""
    You are a cybersecurity expert. A user received the following suspicious email.

    From: {sender}
    Subject: {subject}
    Body: {body}

    Explain in plain English why this email might be a phishing attempt.
    """

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150 
        )

        explanation = response.choices[0].message.content.strip()
        print(explanation)
        return {"explanation": explanation}
    except Exception as e:
        print(f"OpenAI error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get explanation from OpenAI.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
