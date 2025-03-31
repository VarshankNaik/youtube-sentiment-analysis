chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.url && tab.url.includes("youtube.com/watch")) {
    chrome.action.setPopup({ popup: "popup.html" });
  }
});
