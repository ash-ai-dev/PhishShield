chrome.runtime.onInstalled.addListener(() => {
  console.log("PhishShield extension installed.");
});

chrome.identity.getAuthToken({ interactive: true }, function (token) {
  console.log("OAuth token:", token);
});
