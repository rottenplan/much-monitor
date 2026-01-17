import os
import subprocess
import json
import urllib.request
import zipfile

KEXTS_DIR = "/Volumes/EFI/EFI/OC/Kexts"
TMP_DIR = "/tmp/kext_download"

REPOS = [
    {"repo": "acidanthera/FeatureUnlock", "kext": "FeatureUnlock.kext"},
    {"repo": "acidanthera/BrcmPatchRAM", "kext": "BlueToolFixup.kext"}
]

def get_latest_release_url(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        for asset in data['assets']:
            if asset['name'].endswith('.zip') and 'RELEASE' in asset['name'].upper():
                return asset['browser_download_url']
    return None

def install_kexts():
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)
    
    for item in REPOS:
        repo = item['repo']
        target_kext = item['kext']
        print(f"Processing {repo}...")
        
        url = get_latest_release_url(repo)
        if not url:
            print(f"Failed to find release for {repo}")
            continue
        
        zip_path = os.path.join(TMP_DIR, os.path.basename(url))
        print(f"Downloading {url}...")
        urllib.request.urlretrieve(url, zip_path)
        
        print(f"Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(TMP_DIR)
            
        # Find the kext in the extracted files
        for root, dirs, files in os.walk(TMP_DIR):
            if target_kext in dirs:
                src = os.path.join(root, target_kext)
                dst = os.path.join(KEXTS_DIR, target_kext)
                print(f"Installing {target_kext} to {KEXTS_DIR}...")
                if os.path.exists(dst):
                    subprocess.run(["rm", "-rf", dst])
                subprocess.run(["cp", "-R", src, dst])
                break

if __name__ == "__main__":
    install_kexts()
