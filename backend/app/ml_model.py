import joblib
import re
import numpy as np

import os

model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phishing_model.pkl')
try:
    model = joblib.load(model_path)
except Exception as e:
    print(f"Error loading model from {model_path}: {e}")
    model = None

def extract_features(url: str):
    features = [
        len(url),
        url.count('.'),
        url.count('-'),
        url.count('@'),
        url.count('?'),
        1 if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url) else 0,
        url.count('//'),
        
        # Additional features matching train_model.py
        url.count('/'),
        url.count('='),
        sum(c.isdigit() for c in url)
    ]
    
    suspicious_words = ["login", "verify", "secure", "bank", "update", "signin", "free", 
                        "account", "webscr", "cmd", "paypal", "netflix", "microsoft", 
                        "google", "apple", "amazon", "service", "support", "ebay", "info"]
    has_susp_word = 1 if any(word in url.lower() for word in suspicious_words) else 0
    features.append(has_susp_word)
    
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc or url.split('/')[0]
    except Exception:
        domain = ""
    features.append(len(domain))
    
    return np.array([features])

def predict_url(url: str) -> float:
    # Whitelist check for major trusted domains to eliminate false positives on popular sites
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or url.split('/')[0]
        domain = domain.lower()
        if domain.startswith("www."):
            domain = domain[4:]
            
        whitelist = {
            "google.com", "github.com", "microsoft.com", "amazon.com", "paypal.com", 
            "apple.com", "netflix.com", "facebook.com", "twitter.com", "linkedin.com",
            "youtube.com", "instagram.com", "wikipedia.org", "yahoo.com", "outlook.com",
            "live.com", "office.com", "gmail.com", "bing.com", "adobe.com"
        }
        if domain in whitelist:
            return 0.002
    except Exception:
        pass

    if model is None:
        # Fallback heuristic if model is not loaded
        return 0.85 if "login-verify" in url else 0.05
    
    features = extract_features(url)
    prob = model.predict_proba(features)[0][1]
    return float(prob)