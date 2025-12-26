"""
Test script to verify scraper configuration and connectivity
Run this before running the main scraper to check if everything is set up correctly
"""

import asyncio
import sys
from scrape import (
    X_ACCOUNTS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    validate_configuration, send_telegram_message
)
from twscrape import API
from twscrape.logger import set_log_level
import requests
import json

def test_telegram_connection():
    """Test if Telegram bot is configured and working"""
    print("\n" + "="*60)
    print("TESTING TELEGRAM CONNECTION")
    print("="*60)
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Telegram bot token not configured")
        return False
    
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("❌ Telegram chat ID not configured")
        return False
    
    print(f"✓ Bot token configured: {TELEGRAM_BOT_TOKEN[:10]}...")
    print(f"✓ Chat ID configured: {TELEGRAM_CHAT_ID}")
    
    # Test sending a message
    print("\nSending test message to Telegram...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": "🧪 Test message from Twitter Viral Scraper\n\nIf you see this, your Telegram configuration is working correctly!",
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get("ok"):
            print("✅ SUCCESS: Test message sent to Telegram!")
            print(f"   Message ID: {result.get('result', {}).get('message_id', 'N/A')}")
            return True
        else:
            print(f"❌ FAILED: {result.get('description', 'Unknown error')}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Could not connect to Telegram API")
        print(f"   Error: {e}")
        print("\nTroubleshooting:")
        print("  - Check your internet connection")
        print("  - Verify the bot token is correct")
        print("  - Make sure the bot is added to your channel/group")
        return False

async def test_twitter_connection():
    """Test if Twitter accounts are configured and can login"""
    print("\n" + "="*60)
    print("TESTING TWITTER CONNECTION")
    print("="*60)
    
    if not X_ACCOUNTS or len(X_ACCOUNTS) == 0:
        print("❌ No Twitter accounts configured")
        return False
    
    print(f"Found {len(X_ACCOUNTS)} account(s) configured")
    
    # Check configuration
    for i, acc in enumerate(X_ACCOUNTS):
        print(f"\nAccount {i+1}:")
        if acc.get("username") == "YOUR_TWITTER_USERNAME" or not acc.get("username"):
            print(f"  ❌ Username not configured")
            return False
        print(f"  ✓ Username: {acc.get('username')}")
        
        if not acc.get("email"):
            print(f"  ❌ Email not configured")
            return False
        print(f"  ✓ Email: {acc.get('email')}")
    
    # Try to initialize API and add accounts
    print("\nInitializing Twitter API...")
    try:
        set_log_level("INFO")
        api = API()
        
        print("Adding accounts...")
        accounts_added = 0
        for i, acc in enumerate(X_ACCOUNTS):
            try:
                cookies = None
                if "cookies" in acc and acc["cookies"]:
                    if isinstance(acc["cookies"], str):
                        try:
                            cookies = json.loads(acc["cookies"])
                        except json.JSONDecodeError:
                            print(f"  ⚠️  Warning: Invalid cookies format for account {i+1}")
                
                if cookies:
                    await api.pool.add_account(
                        acc["username"],
                        acc["password"],
                        acc["email"],
                        acc["email_password"],
                        cookies=cookies
                    )
                else:
                    await api.pool.add_account(
                        acc["username"],
                        acc["password"],
                        acc["email"],
                        acc["email_password"]
                    )
                accounts_added += 1
                print(f"  ✓ Account {i+1} added: {acc['username']}")
            except Exception as e:
                print(f"  ❌ Failed to add account {i+1}: {e}")
                return False
        
        print(f"\n✓ Successfully added {accounts_added} account(s)")
        
        # Try to login
        print("\nAttempting to login...")
        try:
            await api.pool.login_all()
            print("✅ SUCCESS: All accounts logged in successfully!")
            return True
        except Exception as e:
            error_str = str(e)
            print(f"❌ FAILED: Login error: {e}")
            
            # Check for Cloudflare block
            if "403" in error_str or "Cloudflare" in error_str or "blocked" in error_str.lower():
                print("\n" + "="*60)
                print("⚠️  CLOUDFLARE BLOCK DETECTED")
                print("="*60)
                print("\nTwitter/X is blocking automated login attempts.")
                print("\nSOLUTION: Use cookies from your browser session.")
                print("\nQuick steps:")
                print("1. Open Twitter/X in browser (make sure logged in)")
                print("2. Press F12 → Application tab → Cookies → https://x.com")
                print("3. Copy 'auth_token' and 'ct0' values")
                print("4. Add to scrape.py: \"cookies\": '{\"ct0\": \"...\", \"auth_token\": \"...\"}'")
                print("\nSee CLOUDFLARE_FIX.md for detailed instructions.")
                print("="*60)
            else:
                print("\nTroubleshooting:")
                print("  - Verify your Twitter credentials are correct")
                print("  - Check if 2FA is enabled (may need additional setup)")
                print("  - Try using cookies from an existing session")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Error initializing API: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_twitter_search():
    """Test if we can search for tweets"""
    print("\n" + "="*60)
    print("TESTING TWITTER SEARCH")
    print("="*60)
    
    try:
        set_log_level("INFO")
        api = API()
        
        # Add and login accounts
        for acc in X_ACCOUNTS:
            cookies = None
            if "cookies" in acc and acc["cookies"]:
                if isinstance(acc["cookies"], str):
                    try:
                        cookies = json.loads(acc["cookies"])
                    except:
                        pass
            
            if cookies:
                await api.pool.add_account(
                    acc["username"],
                    acc["password"],
                    acc["email"],
                    acc["email_password"],
                    cookies=cookies
                )
            else:
                await api.pool.add_account(
                    acc["username"],
                    acc["password"],
                    acc["email"],
                    acc["email_password"]
                )
        
        await api.pool.login_all()
        
        # Try a simple search
        print("Testing search with query: 'python lang:en -filter:retweets'")
        print("(Searching for recent Python tweets)...")
        
        tweet_count = 0
        async for tweet in api.search("python lang:en -filter:retweets", limit=5):
            tweet_count += 1
            username = getattr(getattr(tweet, 'user', None), 'username', 'unknown')
            print(f"  ✓ Found tweet {tweet_count}: @{username} - {getattr(tweet, 'rawContent', '')[:50]}...")
            
            if tweet_count >= 3:
                break
        
        if tweet_count > 0:
            print(f"\n✅ SUCCESS: Found {tweet_count} tweet(s)! Twitter search is working.")
            return True
        else:
            print("\n⚠️  WARNING: No tweets found. This might be normal if the search query is too specific.")
            print("   Try running the main scraper - it might still work with your configured query.")
            return True  # Still consider it a success if API works
            
    except Exception as e:
        print(f"❌ FAILED: Search error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("TWITTER VIRAL SCRAPER - CONFIGURATION TEST")
    print("="*60)
    
    # Test 1: Configuration validation
    print("\n" + "="*60)
    print("TESTING CONFIGURATION")
    print("="*60)
    if validate_configuration():
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has errors. Please fix them before running the scraper.")
        sys.exit(1)
    
    # Test 2: Telegram connection
    telegram_ok = test_telegram_connection()
    
    # Test 3: Twitter connection
    twitter_ok = asyncio.run(test_twitter_connection())
    
    # Test 4: Twitter search (only if login worked)
    search_ok = False
    if twitter_ok:
        search_ok = asyncio.run(test_twitter_search())
    else:
        print("\n⚠️  Skipping search test (login failed)")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Configuration: {'✅ PASS' if True else '❌ FAIL'}")
    print(f"Telegram:      {'✅ PASS' if telegram_ok else '❌ FAIL'}")
    print(f"Twitter Login: {'✅ PASS' if twitter_ok else '❌ FAIL'}")
    print(f"Twitter Search:{'✅ PASS' if search_ok else '⚠️  SKIP' if not twitter_ok else '❌ FAIL'}")
    
    if telegram_ok and twitter_ok:
        print("\n🎉 All critical tests passed! Your scraper should work.")
        print("   You can now run: python scrape.py")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before running the scraper.")
        sys.exit(1)

if __name__ == "__main__":
    main()


