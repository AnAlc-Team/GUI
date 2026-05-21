import requests
import json
import zipfile
import os
import sys
import subprocess
from pathlib import Path

#Set the URL prefix
prefix="https://avra-auth.web.app/"

#Get the base directory
base_dir = Path(__file__).parent

#Find file paths
updater_config_path = base_dir / "updater_config.json"
about_path = base_dir / "about.json"

#Read the config file
with open(updater_config_path,'r') as file:
    config = json.load(file)

#Get the data
channel = config["channel"]
auto_update = config["auto_update"]

#Read the about file
with open(about_path,'r') as file:
    about = json.load(file)

#Get the data
current_version = float(about["version"])

# Define your extraction password
zip_password = "neverfind"

def check_version(prefix, channel, current_version, auto_update, base_dir, password):

    print("Checking for updates...")

    #Assemble the URL
    url = prefix + channel + "/" + "version.txt"

    #Send the get request with a timeout in case there is a connection problem
    response = requests.get(url, timeout=10)
    
    #Check if the request was successful
    if response.status_code == 200:

        #Read the version directly from memory
        latest_version = float(response.text.strip())
        
        #Success print
        print("Version successfully fetched!")

    else:

        #Fail print
        print(f"Failed to fetch version. Status code: {response.status_code}")
        return
    
    if latest_version>current_version:

        print("Update needed!")

        #Check if auto-updates are enabled
        if auto_update:

            #Start the download
            download(str(latest_version), prefix, channel, base_dir, password)

    else:

        print("Latest version already installed!")

def download(version, prefix, channel, base_dir, password):

    #Assemble update file URL and download location
    zip_url = prefix + channel + "/" + version + ".zip"
    zip_path = base_dir / "update_temp.zip"
    
    print("Downloading update...")
    
    try:

        #Download the file
        with requests.get(zip_url, stream=True, timeout=15) as response:
            response.raise_for_status()
            
            with open(zip_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
        
    except:

        #In case it failed (symbainei syxna)
        print("Download failed!")
        return
    
    print("Download complete. Extracting files...")
    
    #Extract the files
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:

            #File extraction (Fix 3: use password)
            zip_ref.extractall(path=base_dir, pwd=password.encode('utf-8'))

            print("Extraction complete!")

            updater_script = base_dir / "upgrade.py"
                
            #Start the updater
            subprocess.Popen([sys.executable, str(updater_script)])
            
            #Kill the current proccess
            os._exit(0)

    
    except:
        print("File extraction failed!")
        return
        
    finally:
        #Cleanup
        if zip_path.exists():
            zip_path.unlink()

check_version(prefix,channel,current_version,auto_update,base_dir,zip_password)