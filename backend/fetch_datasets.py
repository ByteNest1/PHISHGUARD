import os
import urllib.request
import zipfile
import io

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def download_file(url, filename):
    filepath = os.path.join(DATA_DIR, filename)
    print(f"Downloading {url} to {filepath}...")
    
    # Set a user-agent to avoid PhishTank/URLhaus blocking default python urllib agent
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    )
    
    with urllib.request.urlopen(req) as response:
        with open(filepath, 'wb') as out_file:
            out_file.write(response.read())
    print(f"Finished downloading {filename}")
    return filepath

def download_and_extract_tranco():
    # Tranco Top 1M list URL
    url = "https://tranco-list.eu/top-1m.csv.zip"
    print(f"Downloading Tranco list from {url}...")
    
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    
    with urllib.request.urlopen(req) as response:
        zip_data = response.read()
        
    print("Extracting Tranco ZIP archive...")
    with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
        csv_filename = z.namelist()[0]
        extracted_path = z.extract(csv_filename, DATA_DIR)
        target_path = os.path.join(DATA_DIR, "tranco.csv")
        if os.path.exists(target_path):
            os.remove(target_path)
        os.rename(extracted_path, target_path)
        print(f"Extracted Tranco list to {target_path}")

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 1. Download PhishTank online-valid.csv
    try:
        download_file("http://data.phishtank.com/data/online-valid.csv", "phishtank.csv")
    except Exception as e:
        print(f"Error downloading PhishTank dataset: {e}")
        print("Falling back to a mirrored/sample backup mechanism if possible...")
        
    # 2. Download URLhaus raw URLs text feed
    try:
        download_file("https://urlhaus.abuse.ch/downloads/text/", "urlhaus.txt")
    except Exception as e:
        print(f"Error downloading URLhaus dataset: {e}")

    # 3. Download Tranco Top 1M list
    try:
        download_and_extract_tranco()
    except Exception as e:
        print(f"Error downloading Tranco dataset: {e}")

if __name__ == "__main__":
    main()
