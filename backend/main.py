import os
import openai
from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Load API key from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your extension's origin later if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model to accept the email details
class EmailData(BaseModel):
    email_body: str
    sender: str
    subject: str
    received_time: str

# Pydantic model for email content in /analyze_email_test endpoint
class EmailContent(BaseModel):
    text: str  # Assuming this is the email body that you're passing in the request

@app.post("/analyze_email_test")
async def analyze_email():
    """Test the endpoint with a random text string."""
    # Just return a simple response for now
    return {"response": "This is a test response to verify the endpoint works."}

@app.post("/check-phishing/")
async def check_phishing(email_data: EmailData):
    # Format the input for OpenAI to ask for a detailed explanation
    input_text = f"""
    This email has been flagged as phishing by a model. Please review the following details and provide a detailed explanation of which specific parts of the email indicate that it is phishing.

    Email Metadata:
    Sender: {email_data.sender}
    Subject: {email_data.subject}
    Received Time: {email_data.received_time}

    Email Body:
    {email_data.email_body}

    Detailed Explanation:
    - What are the suspicious elements in the sender's email address?
    - What content in the subject line could indicate phishing?
    - Are there any signs in the body that suggest malicious intent, such as suspicious links, urgency, or unusual requests?
    - Does the metadata (e.g., time, sender's domain) provide clues to phishing behavior?
    """

    # Send the request to OpenAI
    response = openai.Completion.create(
        engine="text-davinci-003",  # You can also choose a different engine if you want
        prompt=input_text,
        max_tokens=200,  # Increase tokens for a detailed explanation
        temperature=0.7,  # Adjust for more detailed and creative responses
    )

    # Return the response as a string
    result = response.choices[0].text.strip()
    return {"phishing_status": result}

@app.get("/")
async def read_root():
    # Basic HTML form to input email data from the browser
    return HTMLResponse("""
    <html>
        <body>
            <h2>Phishing Email Detector</h2>
            <form action="/check-phishing/" method="post">
                <label for="email_body">Email Body:</label><br>
                <textarea name="email_body" rows="4" cols="50"></textarea><br><br>
                <label for="sender">Sender:</label><br>
                <input type="text" name="sender"><br><br>
                <label for="subject">Subject:</label><br>
                <input type="text" name="subject"><br><br>
                <label for="received_time">Received Time:</label><br>
                <input type="text" name="received_time"><br><br>
                <input type="submit" value="Check Phishing">
            </form>
        </body>
    </html>
    """)
