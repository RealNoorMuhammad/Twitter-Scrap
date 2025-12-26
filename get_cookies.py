"""
Helper script to extract Twitter cookies from browser
This helps bypass Cloudflare protection
"""

import json
import os
import sqlite3
import shutil
from pathlib import Path

def get_chrome_cookies():
    """Extract cookies from Chrome/Edge"""
    cookies = {}
    
    # Common Chrome/Edge cookie locations
    cookie_paths = [
        os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Cookies"),
        os.path.expanduser("~/AppData/Local/Microsoft/Edge/User Data/Default/Cookies"),
        os.path.expanduser("~/.config/google-chrome/Default/Cookies"),  # Linux
        os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies"),  # Mac
    ]
    
    cookie_db = None
    for path in cookie_paths:
        if os.path.exists(path):
            try:
                # Copy the database (Chrome locks it)
                temp_db = path + ".temp"
                shutil.copy2(path, temp_db)
                cookie_db = temp_db
                break
            except Exception as e:
                print(f"Could not access {path}: {e}")
                continue
    
    if not cookie_db:
        return None
    
    try:
        conn = sqlite3.connect(cookie_db)
        cursor = conn.cursor()
        
        # Get cookies for x.com and twitter.com
        cursor.execute("""
            SELECT name, value, host_key 
            FROM cookies 
            WHERE (host_key LIKE '%x.com%' OR host_key LIKE '%twitter.com%')
            AND (name = 'auth_token' OR name = 'ct0')
        """)
        
        for row in cursor.fetchall():
            name, value, host = row
            cookies[name] = value
        
        conn.close()
        os.remove(cookie_db)
        
        if 'auth_token' in cookies and 'ct0' in cookies:
            return cookies
    except Exception as e:
        print(f"Error reading cookies: {e}")
        if os.path.exists(cookie_db):
            os.remove(cookie_db)
    
    return None

def get_firefox_cookies():
    """Extract cookies from Firefox"""
    # Firefox uses JSON format
    profile_paths = [
        os.path.expanduser("~/AppData/Roaming/Mozilla/Firefox/Profiles"),
        os.path.expanduser("~/.mozilla/firefox"),  # Linux
        os.path.expanduser("~/Library/Application Support/Firefox/Profiles"),  # Mac
    ]
    
    for base_path in profile_paths:
        if not os.path.exists(base_path):
            continue
        
        # Find default profile
        for item in os.listdir(base_path):
            if item.endswith('.default') or item.endswith('.default-release'):
                profile_path = os.path.join(base_path, item)
                cookies_file = os.path.join(profile_path, "cookies.sqlite")
                
                if os.path.exists(cookies_file):
                    try:
                        conn = sqlite3.connect(cookies_file)
                        cursor = conn.cursor()
                        
                        cursor.execute("""
                            SELECT name, value, host 
                            FROM moz_cookies 
                            WHERE (host LIKE '%x.com%' OR host LIKE '%twitter.com%')
                            AND (name = 'auth_token' OR name = 'ct0')
                        """)
                        
                        cookies = {}
                        for row in cursor.fetchall():
                            name, value, host = row
                            cookies[name] = value
                        
                        conn.close()
                        
                        if 'auth_token' in cookies and 'ct0' in cookies:
                            return cookies
                    except Exception as e:
                        print(f"Error reading Firefox cookies: {e}")
    
    return None

def main():
    print("=" * 60)
    print("Twitter Cookie Extractor")
    print("=" * 60)
    print("\nThis script will try to extract Twitter cookies from your browser.")
    print("Make sure you're logged into Twitter/X in your browser first!\n")
    
    cookies = None
    
    # Try Chrome/Edge first
    print("Trying Chrome/Edge...")
    cookies = get_chrome_cookies()
    
    # Try Firefox if Chrome didn't work
    if not cookies:
        print("Trying Firefox...")
        cookies = get_firefox_cookies()
    
    if cookies:
        print("\n✅ Found cookies!")
        print("\nAdd this to your scrape.py in the X_ACCOUNTS section:")
        print("-" * 60)
        cookie_json = json.dumps(cookies)
        print(f'"cookies": {json.dumps(cookie_json)}')
        print("-" * 60)
        print("\nExample:")
        print('"cookies": \'{"ct0": "' + cookies.get('ct0', '')[:20] + '...", "auth_token": "' + cookies.get('auth_token', '')[:20] + '..."}\'')
        
        # Save to file
        with open("cookies_output.txt", "w") as f:
            f.write(f'"cookies": {json.dumps(cookie_json)}\n')
        print("\n✅ Cookies also saved to cookies_output.txt")
    else:
        print("\n❌ Could not find Twitter cookies automatically.")
        print("\nManual method:")
        print("1. Open Twitter/X in your browser (make sure you're logged in)")
        print("2. Press F12 to open Developer Tools")
        print("3. Go to Application tab (Chrome) or Storage tab (Firefox)")
        print("4. Click Cookies → https://x.com")
        print("5. Find 'auth_token' and 'ct0' values")
        print("6. Add them to scrape.py as:")
        print('   "cookies": \'{"ct0": "YOUR_CT0", "auth_token": "YOUR_AUTH_TOKEN"}\'')

if __name__ == "__main__":
    main()


