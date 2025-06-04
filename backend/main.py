import os
import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
import openai
from typing import List

# Load environment variables
load_dotenv("openAI.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load ML model
model = joblib.load("data/saved_models/train_embed_50_Ensemble.joblib") 

# Load sentence embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# FastAPI app setup
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper to predict email phishing status
def predict_emails(email_texts: list[str]):
    embedding_array = embedding_model.encode(email_texts, batch_size=32, show_progress_bar=False)
    print(f"✅ Embeddings shape: {embedding_array.shape}")

    # Use model's expected feature names as columns
    columns = list(map(str, model.feature_names_in_)) if hasattr(model, 'feature_names_in_') else [str(i) for i in range(embedding_array.shape[1])]
    embedding_df = pd.DataFrame(embedding_array, columns=columns)

    print(f"✅ Embedding DataFrame shape: {embedding_df.shape}")
    print("Model expects:", model.feature_names_in_)
    print("DataFrame columns:", embedding_df.columns.tolist())
    print("Column equality:", all(str(c1) == str(c2) for c1, c2 in zip(model.feature_names_in_, embedding_df.columns)))

    
    preds = model.predict(embedding_df)
    return preds



# --- Main endpoint ---

class EmailItem(BaseModel):
    messageId: str
    from_: str = Field(..., alias="from")
    subject: str
    body: str

@app.post("/api/emails")
async def receive_emails(emails: List[EmailItem]):
    try:
        # 1. Combine and normalize subject + body for all emails
        full_texts = [f"{email.subject} {email.body}".lower() for email in emails]

        # 🔍 Debug: show inputs to embedding model
        print("\n📨 Full normalized text used for embedding:\n")
        for i, text in enumerate(full_texts):
            print(f"Email {i+1}: {text}\n{'-'*40}")

        # 2. Generate embeddings
        embeddings = embedding_model.encode(full_texts, batch_size=32, show_progress_bar=False)

        # 3. Convert to DataFrame for model prediction
        columns = list(map(str, model.feature_names_in_)) if hasattr(model, 'feature_names_in_') else [str(i) for i in range(embeddings.shape[1])]
        df = pd.DataFrame(embeddings, columns=columns)

        # 4. Predict phishing status
        predictions = model.predict(df)

        # 5. Format results
        results = []
        for email, prediction in zip(emails, predictions):
            label = "Phishing" if prediction == 1 else "Not Phishing"
            results.append({
                "email": email.dict(),
                "prediction": label
            })
            print(email)
            print(prediction)


        return JSONResponse(content={"results": results})

    except Exception as e:
        print("❌ Error in receive_emails:", e)
        raise HTTPException(status_code=500, detail="Failed to process emails")


"""
@app.post("/email")
async def receive_emails(request: Request):
    try:
        raw_body = await request.json()
        print("📨 Raw request body received:", raw_body)

        # Optionally log the type of each entry for clarity
        if isinstance(raw_body, list):
            for i, item in enumerate(raw_body):
                print(f"Item {i} keys: {list(item.keys())}")
        else:
            print("❌ Expected a list but got:", type(raw_body))

        # Manually parse to Pydantic model list
        emails = [EmailData(**item) for item in raw_body]

    except Exception as e:
        print("❌ Failed to parse request body:", e)
        raise HTTPException(status_code=400, detail="Invalid request format.")
    
    results = []
    print("hi")
    # Combine subject + body for embedding
    full_texts = [f"{email.subject}\n\n{email.email_body}" for email in emails]
    print("\n📨 Full text used for embedding:\n")
    for i, text in enumerate(full_texts):
        print(f"Email {i}:\n{text}\n{'-'*40}")

    print("bye")
    print("Model expects features:", model.feature_names_in_)
    predictions = predict_emails(full_texts)
    print("byebye")
    print(predictions)

    for email, prediction in zip(emails, predictions):
        label = "Phishing" if prediction == 1 else "Not Phishing"

        # Optional explanation
        if label == "Phishing":
            try:
                explanation = await explain_phishing({
                    "sender": email.sender,
                    "subject": email.subject,
                    "body": email.email_body
                })
                explanation = explanation.get("explanation", "")
            except Exception:
                explanation = "Failed to generate explanation."
        else:
            explanation = "This email does not appear to be phishing."

        results.append({
            "prediction": label,
            "explanation": explanation,
            "email": email.dict()
        })

    return JSONResponse(content={"results": results})
"""

# --- Explanation endpoint (OpenAI) ---
@app.post("/api/explain")
async def explain_phishing(payload: dict):
    sender = payload.get("sender", "")
    subject = payload.get("subject", "")
    body = payload.get("body", "")

    prompt = f"""
    You are a cybersecurity expert. A user received the following suspicious email:

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
            max_tokens=100
        )
        explanation = response.choices[0].message.content.strip()
        return {"explanation": explanation}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get explanation from OpenAI.")


if __name__ == "__main__":
    # Generate some dummy emails for testing
    test_emails = [
        "Urgent: Your account has been compromised. Please verify your identity immediately.",
        "Meeting reminder: Let's catch up tomorrow at 3pm in the conference room.",
        "Congratulations! You've won a $1000 gift card. Click here to claim your prize.",
        "Weekly newsletter: Updates from the product team and upcoming events.",
        "Security alert: Suspicious login detected from an unknown device."
    ]

    print("=== Testing embedding and prediction on sample emails ===")
    predictions = predict_emails(test_emails)

    for i, (email_text, pred) in enumerate(zip(test_emails, predictions)):
        label = "Phishing" if pred == 1 else "Not Phishing"
        print(f"Email {i+1} prediction: {label}")
        print(f"Text: {email_text}\n{'-'*50}")