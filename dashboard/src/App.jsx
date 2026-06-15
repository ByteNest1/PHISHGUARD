import React, { useState, useEffect } from 'react';

export default function App() {
  const [logs, setLogs] = useState([]);

  const fetchLogs = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8001/api/v1/logs');
      const data = await res.json();
      setLogs(data);
    } catch (err) {
      console.error("Failed fetching threat feeds:", err);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 4000);
    return () => clearInterval(interval);
  }, []);

  const downloadIoCs = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(logs, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", "phishguard_ioc_export.json");
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="min-h-screen p-8">
      <header className="flex justify-between items-center border-b pb-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">PhishGuard Intelligence Hub</h1>
          <p className="text-sm text-slate-500">Real-time telemetry and network operations overview</p>
        </div>
        <button onClick={downloadIoCs} className="bg-slate-900 text-white px-4 py-2 rounded text-sm font-medium hover:bg-slate-800 transition">
          Export IoC Blueprint
        </button>
      </header>

      <main className="grid grid-cols-1 gap-6">
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4">Interception Logs</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-slate-50 border-b text-slate-600 font-medium">
                  <th className="p-3">Timestamp</th>
                  <th className="p-3">Target Address</th>
                  <th className="p-3">Risk Assessment</th>
                  <th className="p-3">ML Threat Weight</th>
                  <th className="p-3">Inference Delay</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="p-4 text-center text-slate-400">No active browser navigation intercepted yet.</td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id} className="border-b hover:bg-slate-50 transition">
                      <td className="p-3 whitespace-nowrap text-slate-500">{log.timestamp}</td>
                      <td className="p-3 max-w-xs truncate font-mono text-xs">{log.url}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${log.risk_level === 'HIGH' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                          {log.risk_level}
                        </span>
                      </td>
                      <td className="p-3 font-medium">{(log.ml_score * 100).toFixed(2)}%</td>
                      <td className="p-3 text-slate-500 font-mono text-xs">{log.latency_ms}ms</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}