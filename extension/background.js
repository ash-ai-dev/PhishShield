// background.js
import { fetchEmailsByLabel, fetchEmailById } from "./gmailAPI.js";

chrome.storage.local.get(["phishingLabelId"], async (result) => {
  const labelId = result.phishingLabelId;

  if (!labelId) {
    console.error("No label ID saved. Run fetchAndSaveLabelId() first.");
    return;
  }

  try {
    const messages = await fetchEmailsByLabel(labelId);
    console.log(`Found ${messages.length} messages in label ${labelId}`);

    // Optional: fetch details for first message
    if (messages.length > 0) {
      const firstMsg = await fetchEmailById(messages[0].id);
      console.log("First message details:", firstMsg);
    }
  } catch (err) {
    console.error(err);
  }
});

async function fetchAndSaveLabelId(targetLabelName = "PhishShield") {
  chrome.identity.getAuthToken({ interactive: true }, async (token) => {
    if (chrome.runtime.lastError) {
      console.error("Auth failed: " + chrome.runtime.lastError.message);
      return;
    }
    if (!token) {
      console.error("No token received.");
      return;
    }

    const res = await fetch(
      "https://gmail.googleapis.com/gmail/v1/users/me/labels",
      {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/json",
        },
      }
    );

    if (!res.ok) {
      console.error("API request failed: " + res.statusText);
      return;
    }

    const data = await res.json();
    if (!data.labels || data.labels.length === 0) {
      console.error("No labels found.");
      return;
    }

    const label = data.labels.find((l) => l.name === targetLabelName);

    if (label) {
      console.log(`Found label "${targetLabelName}" with ID: ${label.id}`);

      // Save label ID for later use
      chrome.storage.local.set({ phishingLabelId: label.id }, () => {
        console.log("Phishing label ID saved:", label.id);
      });
    } else {
      console.error(`Label "${targetLabelName}" not found.`);
    }
  });
}

// Example call (you can trigger this from background event or message)
fetchAndSaveLabelId();
