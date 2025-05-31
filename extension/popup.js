document.getElementById("fetchData").addEventListener("click", () => {
  const responseDiv = document.getElementById("response");
  const predictionDiv = document.getElementById("prediction");
  const explanationDiv = document.getElementById("explanation");

  responseDiv.textContent = "Authenticating with Google...";

  chrome.identity.getAuthToken({ interactive: true }, (token) => {
    if (chrome.runtime.lastError) {
      console.error("Auth error:", chrome.runtime.lastError.message);
      responseDiv.textContent = "Authentication failed.";
      return;
    }

    console.log("OAuth token:", token);
    responseDiv.textContent = "Fetching latest Gmail message...";

    // Step 1: Fetch most recent message ID
    fetch(
      "https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=1",
      {
        headers: {
          Authorization: "Bearer " + token,
        },
      }
    )
      .then((res) => res.json())
      .then((data) => {
        const messageId = data?.messages?.[0]?.id;
        if (!messageId) {
          responseDiv.textContent = "No recent emails found.";
          return Promise.reject("No message ID retrieved.");
        }

        // Step 2: Fetch full message details
        return fetch(
          `https://gmail.googleapis.com/gmail/v1/users/me/messages/${messageId}?format=full`,
          {
            headers: {
              Authorization: "Bearer " + token,
            },
          }
        );
      })
      .then((res) => res.json())
      .then((message) => {
        if (!message || !message.payload) {
          responseDiv.textContent = "Unable to retrieve email content.";
          return;
        }

        const headers = message.payload.headers || [];
        const subject =
          headers.find((h) => h.name === "Subject")?.value || "No subject";
        const sender =
          headers.find((h) => h.name === "From")?.value || "Unknown sender";
        const emailBody = message.snippet || "";
        const receivedTime = new Date(
          parseInt(message.internalDate)
        ).toISOString();

        responseDiv.textContent = `Analyzing: "${subject}"...`;
        console.log("Full Gmail message:", message);

        // Step 3: Send email data to FastAPI
        return fetch("http://127.0.0.1:8000/email", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email_body: emailBody,
            sender: sender,
            subject: subject,
            received_time: receivedTime,
          }),
        });
      })
      .then((res) => res.json())
      .then((data) => {
        console.log("FastAPI response:", data);

        predictionDiv.textContent = `Prediction: ${data.prediction}`;
        explanationDiv.textContent = `Explanation: ${data.explanation}`;
        responseDiv.textContent = "Analysis complete.";
      })
      .catch((error) => {
        console.error("Error:", error);
        responseDiv.textContent =
          "An error occurred. Check console for details.";
      });
  });
});
