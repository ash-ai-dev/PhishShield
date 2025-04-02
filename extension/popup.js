document.getElementById("fetchData").addEventListener("click", async () => {
  const responseDiv = document.getElementById("response");
  responseDiv.textContent = "Loading...";

  // Set up the test email content (as per your FastAPI endpoint)
  const testEmail = {
    text: "Hello, I need you to urgently verify your account. Click the link below to reset your password.",
  };

  // Send the POST request to the FastAPI backend
  try {
    const response = await fetch("http://127.0.0.1:8000/analyze_email_test", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(testEmail),
    });

    const data = await response.json();
    responseDiv.textContent = data.response;
  } catch (error) {
    responseDiv.textContent = "Error fetching data from FastAPI endpoint";
    console.error(error);
  }
});
