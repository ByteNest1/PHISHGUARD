import os
import re
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def extract_lexical_features(url):
    """Extracts identical features used during real-time inference."""
    features = []
    features.append(len(url))
    features.append(url.count('.'))
    features.append(url.count('-'))
    features.append(url.count('@'))
    features.append(url.count('?'))
    features.append(1 if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url) else 0)
    features.append(url.count('//'))
    
    # Additional high-predictive features to achieve >=95% accuracy
    features.append(url.count('/'))
    features.append(url.count('='))
    features.append(sum(c.isdigit() for c in url))
    
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
    
    return features

def load_malicious_urls():
    urls = []
    
    # 1. Load from PhishTank
    phishtank_path = os.path.join(DATA_DIR, "phishtank.csv")
    if os.path.exists(phishtank_path):
        print("Loading phishing URLs from PhishTank...")
        try:
            df_pt = pd.read_csv(phishtank_path)
            pt_urls = df_pt['url'].dropna().tolist()
            urls.extend(pt_urls)
            print(f"Loaded {len(pt_urls)} URLs from PhishTank.")
        except Exception as e:
            print(f"Error reading PhishTank: {e}")
            
    # 2. Load from URLhaus
    urlhaus_path = os.path.join(DATA_DIR, "urlhaus.txt")
    if os.path.exists(urlhaus_path):
        print("Loading malicious URLs from URLhaus...")
        try:
            uh_urls = []
            with open(urlhaus_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        uh_urls.append(line)
            urls.extend(uh_urls)
            print(f"Loaded {len(uh_urls)} URLs from URLhaus.")
        except Exception as e:
            print(f"Error reading URLhaus: {e}")
            
    # Remove duplicates
    urls = list(set(urls))
    print(f"Total unique malicious URLs: {len(urls)}")
    return urls

def load_benign_urls(num_required):
    urls = []
    tranco_path = os.path.join(DATA_DIR, "tranco.csv")
    if os.path.exists(tranco_path):
        print("Loading benign domains from Tranco...")
        try:
            # Tranco format is rank,domain
            df_tr = pd.read_csv(tranco_path, header=None, nrows=num_required * 2)
            domains = df_tr[1].dropna().tolist()
            
            # Prepend random protocol/www to mimic actual browser URLs
            np.random.seed(42)
            for i, domain in enumerate(domains):
                rand = np.random.rand()
                if rand < 0.5:
                    url = f"https://{domain}"
                elif rand < 0.7:
                    url = f"http://{domain}"
                elif rand < 0.9:
                    url = f"https://www.{domain}"
                else:
                    url = f"http://www.{domain}"
                
                # Randomly append common paths/queries to mimic full URLs
                rand_path = np.random.rand()
                if rand_path < 0.3:
                    url += "/index.html"
                elif rand_path < 0.5:
                    url += "/search?q=query"
                elif rand_path < 0.6:
                    url += "/login"
                elif rand_path < 0.7:
                    url += "/main/home"
                
                urls.append(url)
                if len(urls) >= num_required:
                    break
            print(f"Loaded {len(urls)} benign URLs from Tranco.")
        except Exception as e:
            print(f"Error reading Tranco: {e}")
    return urls

def main():
    print("Loading datasets for PhishGuard training...")
    malicious_urls = load_malicious_urls()
    
    # We want a balanced dataset, so we match the number of benign URLs to malicious URLs
    num_malicious = len(malicious_urls)
    if num_malicious == 0:
        print("Error: No malicious URLs found. Cannot train.")
        return
        
    benign_urls = load_benign_urls(num_malicious)
    
    # Create final balanced dataset
    data = []
    for url in benign_urls:
        data.append(extract_lexical_features(url) + [0])
    for url in malicious_urls:
        data.append(extract_lexical_features(url) + [1])
        
    cols = ['url_len', 'dots', 'hyphens', 'at_symbols', 'queries', 'contains_ip', 'double_slashes', 
            'slashes', 'equals', 'digits', 'has_suspicious_word', 'domain_len', 'label']
    df = pd.DataFrame(data, columns=cols)
    
    # Shuffle dataset
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    X = df.drop(columns=['label'])
    y = df['label']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training XGBoost Classifier...")
    model = xgb.XGBClassifier(
        use_label_encoder=False, 
        eval_metric='logloss',
        max_depth=6,
        n_estimators=150,
        learning_rate=0.1,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    # Evaluation
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print("\n" + "="*50)
    print(f"MODEL TRAINING COMPLETE.")
    print(f"Evaluated Test Accuracy: {acc * 100:.2f}%")
    print("="*50)
    print("\nClassification Report:")
    print(classification_report(y_test, preds))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, preds))
    
    # Check if target accuracy is met
    if acc >= 0.95:
        print("\nTarget accuracy of >= 95% met successfully!")
    else:
        print("\nWarning: Target accuracy of >= 95% was not met. You may need to tune features.")
        
    os.makedirs('app', exist_ok=True)
    joblib.dump(model, 'app/phishing_model.pkl')
    print("\nModel serialized successfully inside 'app/phishing_model.pkl'")

if __name__ == "__main__":
    main()