chrome.webNavigation.onBeforeNavigate.addListener(async (details) => {
  // Only monitor top-level main frame requests, ignore tracking/ad frames
  if (details.frameId !== 0) return;

  const url = details.url;
  if (url.startsWith("chrome://") || url.startsWith("about:")) return;

  try {
    const response = await fetch("http://127.0.0.1:8001/api/v1/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url })
    });
    
    const data = await response.json();
    
    if (data.risk_level === "HIGH") {
      console.warn(`[PhishGuard Warning]: Malicious target detected -> ${url}`);
      // Simple non-intrusive runtime system alert to act as safety blocking boundary
      chrome.tabs.sendMessage(details.tabId, { action: "alert_user", url: url });
    }
  } catch (err) {
    console.error("PhishGuard Backend connection offline:", err);
  }
});