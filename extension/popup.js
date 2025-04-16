document.getElementById("fetchData").addEventListener("click", () => {
  const responseDiv = document.getElementById("response");
  responseDiv.textContent = "Authenticating with Google...";

  chrome.identity.getAuthToken({ interactive: true }, (token) => {
    if (chrome.runtime.lastError) {
      console.error("Auth error:", chrome.runtime.lastError);
      responseDiv.textContent = "Authentication failed.";
      return;
    }

    console.log("OAuth token:", token);
    responseDiv.textContent = "Fetching email...";

    // Fetch list of messages
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
        if (!data.messages || data.messages.length === 0) {
          responseDiv.textContent = "No emails found.";
          return;
        }

        const messageId = data.messages[0].id;

        // Fetch the message content
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
        const headers = message.payload.headers;
        const subjectHeader = headers.find((h) => h.name === "Subject");
        const senderHeader = headers.find((h) => h.name === "From");
        const subject = subjectHeader ? subjectHeader.value : "No subject";
        const sender = senderHeader ? senderHeader.value : "Unknown sender";
        const emailBody = message.snippet;
        const receivedTime = new Date(
          parseInt(message.internalDate)
        ).toISOString();

        responseDiv.textContent = `Latest email subject: ${subject}`;
        console.log("Full message:", message);

        // Send email data to FastAPI server
        fetch("http://127.0.0.1:8000/email", {
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
        })
          .then((response) => response.json())
          .then((data) => {
            console.log("Data sent to FastAPI:", data);

            document.getElementById("prediction").textContent = data.prediction;
            document.getElementById("explanation").textContent =
              data.explanation;
          })
          .catch((error) => {
            console.error("Error sending data to FastAPI:", error);
          });
      })
      .catch((error) => {
        console.error("Error fetching Gmail:", error);
        responseDiv.textContent = "Error fetching Gmail message.";
      });
  });
});
