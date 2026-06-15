from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import time

from app.ml_model import predict_url
from app.services import check_virus_total, calculate_typosquatting, perform_dns_lookup

app = FastAPI(title="PhishGuard Security Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global memory log acting as datastore for Dashboard telemetry
scan_logs = []

class URLPayload(BaseModel):
    url: str

@app.post("/api/v1/analyze")
async def analyze_url(payload: URLPayload):
    start_time = time.time()
    url = payload.url
    
    # Trigger all independent analytical pipelines in parallel via asyncio.gather
    ml_task = asyncio.to_thread(predict_url, url)
    vt_task = check_virus_total(url)
    typo_task = calculate_typosquatting(url)
    dns_task = perform_dns_lookup(url)
    
    ml_score, vt_result, typo_result, dns_result = await asyncio.gather(
        ml_task, vt_task, typo_task, dns_task
    )
    
    # High level risk calculation heuristics
    is_malicious = ml_score > 0.7 or vt_result["positives"] > 0 or typo_result["is_typosquat"]
    risk_level = "HIGH" if is_malicious else "LOW"
    
    execution_latency_ms = (time.time() - start_time) * 1000
    
    log_entry = {
        "id": len(scan_logs) + 1,
        "url": url,
        "risk_level": risk_level,
        "ml_score": round(ml_score, 4),
        "typosquatting": typo_result,
        "dns": dns_result,
        "virus_total": vt_result,
        "latency_ms": round(execution_latency_ms, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    scan_logs.append(log_entry)
    
    return log_entry

@app.get("/api/v1/logs")
async def get_logs():
    return scan_logs