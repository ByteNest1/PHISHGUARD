document.addEventListener("DOMContentLoaded", async () => {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url) {
      document.getElementById("url-text").textContent = tab.url;
      
      // Let's call the backend api to show risk assessment inside the popup itself
      const response = await fetch("http://127.0.0.1:8001/api/v1/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: tab.url })
      });
      const data = await response.json();
      
      const statusDiv = document.querySelector(".status");
      if (data.risk_level === "HIGH") {
        statusDiv.textContent = `Warning: High Risk (${(data.ml_score * 100).toFixed(0)}%)`;
        statusDiv.className = "status danger";
        statusDiv.style.background = "#fee2e2";
        statusDiv.style.color = "#991b1b";
      } else {
        statusDiv.textContent = "URL Assessed: Safe";
        statusDiv.className = "status safe";
        statusDiv.style.background = "#dcfce7";
        statusDiv.style.color = "#166534";
      }
    } else {
      document.getElementById("url-text").textContent = "No active tab detected";
    }
  } catch (err) {
    document.getElementById("url-text").textContent = "Error loading status";
  }
});
