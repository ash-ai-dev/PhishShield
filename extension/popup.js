import {
  fetchEmailsByLabel,
  fetchEmailById,
  extractSimplifiedMessages,
} from "./gmailAPI.js";

const CACHE_KEY = "emailCache";

async function loadEmails() {
  const emailListDiv = document.getElementById("emailList");
  emailListDiv.innerHTML = "Loading emails...";

  try {
    const { phishingLabelId: labelId } = await new Promise((resolve) =>
      chrome.storage.local.get(["phishingLabelId"], resolve)
    );

    if (!labelId) {
      emailListDiv.innerText =
        "PhishShield label not found. Please initialize the extension.";
      return;
    }

    // Try to load cached data
    const cache = await new Promise((resolve) =>
      chrome.storage.local.get([CACHE_KEY], (result) =>
        resolve(result[CACHE_KEY])
      )
    );

    if (cache && Object.keys(cache).length > 0) {
      renderEmailList(cache);
      console.log("Loaded emails from cache.");
      return;
    }

    // No cache, fetch fresh emails and predictions
    const messages = await fetchEmailsByLabel(labelId);
    const simplifiedMessages = await extractSimplifiedMessages(labelId);

    const res = await fetch("http://127.0.0.1:8000/api/emails", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(simplifiedMessages),
    });

    const { results } = await res.json();

    const cacheMap = {};
    results.forEach((r) => {
      const msgId = r.email.messageId;
      cacheMap[msgId] = {
        label: r.prediction,
        from: r.email.from,
        subject: r.email.subject,
        body: r.email.body,
      };
    });

    // Save cache
    await new Promise((resolve) =>
      chrome.storage.local.set({ [CACHE_KEY]: cacheMap }, resolve)
    );

    renderEmailList(cacheMap);
  } catch (err) {
    console.error("❗ Error:", err);
    emailListDiv.innerText = "An error occurred: " + err.message;
  }
}

function renderEmailList(cacheMap) {
  const emailListDiv = document.getElementById("emailList");
  emailListDiv.innerHTML = "";

  Object.entries(cacheMap).forEach(([msgId, data]) => {
    const emailDiv = document.createElement("div");
    emailDiv.style.borderBottom = "1px solid #ddd";
    emailDiv.style.marginBottom = "10px";
    emailDiv.style.cursor = "pointer";
    emailDiv.style.padding = "8px";
    emailDiv.style.backgroundColor =
      data.label === "Phishing" ? "#ffd9d9" : "#d8f8d3";

    emailDiv.innerHTML = `<strong>${data.subject}</strong><p>${data.body.slice(
      0,
      100
    )}...</p>`;

    emailDiv.addEventListener("click", () => {
      chrome.storage.local.set({ selectedEmail: data }, () => {
        chrome.tabs.create({ url: chrome.runtime.getURL("details.html") });
      });
    });

    emailListDiv.appendChild(emailDiv);
  });
}

// Clear cache handler
document.getElementById("clearCache").addEventListener("click", async () => {
  await new Promise((resolve) =>
    chrome.storage.local.remove(CACHE_KEY, resolve)
  );
  // Optionally clear UI immediately
  document.getElementById("emailList").innerHTML =
    "Cache cleared. Loading fresh emails...";
  // Reload fresh emails
  loadEmails();
});

// Load emails automatically on popup open
loadEmails();

// Manual load button
document
  .getElementById("loadEmails")
  .addEventListener("click", () => loadEmails());
