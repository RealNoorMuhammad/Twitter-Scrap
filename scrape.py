import asyncio
from datetime import datetime, timedelta
from twscrape import API
from twscrape.logger import set_log_level
import requests
import json
import re
import os
import aiohttp
from urllib.parse import urlparse

# ============================================================================
# CONFIGURATION - REPLACE THESE VALUES WITH YOUR OWN
# ============================================================================

# Twitter/X Account Credentials
# You can add multiple accounts for better rate limits
X_ACCOUNTS = [
    {
        "username": "jordanbania",
        "password": "8k7m1lqanyl0",
        "email": "haroldthompson@epithic.com",
        "email_password": "pfzwjoqgS9302",
        # Optional: Add cookies for already logged-in accounts
        # "cookies": '{"ct0": "your_ct0_token", "auth_token": "your_auth_token"}'
    },
    # Add more accounts if needed:
    # {
    #     "username": "another_account",
    #     "password": "another_password",
    #     "email": "another@example.com",
    #     "email_password": "email_password"
    # }
]

# Telegram Bot Configuration
# Get your bot token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN = "8530405784:AAGlJDxr2IOI4GGqWWsdHxKQ0XY0rJMlhgs"
# Get your chat/channel ID (use @userinfobot or @getidsbot)
TELEGRAM_CHAT_ID = "-1003652909016"

# ============================================================================
# SCRAPING SETTINGS - CUSTOMIZE THESE AS NEEDED
# ============================================================================

# Maximum age of tweets to scrape (in days)
MAX_AGE_DAYS = 1

# Minimum number of likes for a tweet to be considered viral
MIN_LIKES = 5000

# Tweet type filtering options:
# - "media_only": Only tweets with images/videos/GIFs
# - "text_only": Only text tweets (no media)
# - "all": All tweets (both media and text)
TWEET_TYPES = "media_only"

# How often to check for new tweets (in minutes)
CHECK_INTERVAL_MINUTES = 10

# Enable continuous monitoring (True) or run once (False)
CONTINUOUS_MONITORING = True

# File to track already-sent tweets (prevents duplicates)
SENT_TWEETS_FILE = "sent_tweets.txt"

# ============================================================================
# HELPER FUNCTIONS - NO NEED TO MODIFY BELOW THIS LINE
# ============================================================================

async def validate_media_url(url: str) -> bool:
    """Check if media URL is accessible"""
    if not url:
        return False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as response:
                return response.status == 200
    except asyncio.TimeoutError:
        print(f"Media validation timeout for {url}")
        return False
    except Exception as e:
        print(f"Media validation failed for {url}: {e}")
        return False

async def send_telegram_photo(chat_id: str, photo_url: str, caption: str, bot_token: str):
    """Send photo to Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "MarkdownV2"
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        response_json = response.json()
        if not response_json.get("ok"):
            print(f"ERROR: Telegram sendPhoto failed: {response_json.get('description', 'No description')}")
            return False
        return True
    except Exception as e:
        print(f"ERROR: Failed to send photo: {e}")
        return False

async def send_telegram_video(chat_id: str, video_url: str, caption: str, bot_token: str):
    """Send video to Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
    payload = {
        "chat_id": chat_id,
        "video": video_url,
        "caption": caption,
        "parse_mode": "MarkdownV2"
    }
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        response_json = response.json()
        if not response_json.get("ok"):
            print(f"ERROR: Telegram sendVideo failed: {response_json.get('description', 'No description')}")
            return False
        return True
    except Exception as e:
        print(f"ERROR: Failed to send video: {e}")
        return False

async def send_telegram_message_with_media(chat_id: str, message: str, bot_token: str, media_items=None):
    """Send message with media, fallback to text if media fails"""
    if not media_items:
        return await send_telegram_message(chat_id, message, bot_token)
    
    # Try sending each media item
    for media_item in media_items:
        media_type = getattr(media_item, 'type', 'unknown').lower()
        media_url = getattr(media_item, 'url', None)
        
        if not media_url:
            continue
            
        print(f"Validating media URL: {media_url}")
        if not await validate_media_url(media_url):
            print(f"Media URL not accessible, skipping: {media_url}")
            continue
        
        # Send based on type
        if media_type in ['photo', 'image']:
            print(f"Sending as photo...")
            success = await send_telegram_photo(chat_id, media_url, message, bot_token)
            if success:
                return True
        elif media_type in ['video', 'animated_gif']:
            print(f"Sending as video...")
            success = await send_telegram_video(chat_id, media_url, message, bot_token)
            if success:
                return True
    
    # Fallback to text with media links
    print("Media failed, sending as text with links...")
    media_links = []
    for media_item in media_items:
        media_type = getattr(media_item, 'type', 'unknown')
        media_url = getattr(media_item, 'url', None)
        if media_url:
            media_link = create_safe_url_link(media_url, f"{media_type}")
            media_links.append(f"  \\- {media_link}")
    
    if media_links:
        message += "\n\n*Media*:\n" + "\n".join(media_links)
    
    return await send_telegram_message(chat_id, message, bot_token)

async def send_telegram_message(chat_id: str, message: str, bot_token: str):
    """Send text message to Telegram"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        response_json = response.json()
        if not response_json.get("ok"):
            print(f"ERROR: Telegram API error: {response_json.get('description', 'No description')}. Response: {response.text}")
            return False
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to send message: {e}. Response text: {getattr(e.response, 'text', 'No response text')}")
        return False

def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2"""
    if not text:
        return ""
    
    text = str(text)
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def create_safe_url_link(url: str, display_text: str = None) -> str:
    """Create safe MarkdownV2 formatted link"""
    if not url:
        return ""
    
    if not display_text:
        display_text = "Link"
    
    safe_display_text = escape_markdown_v2(display_text)
    return f"[{safe_display_text}]({url})"

def load_sent_tweets() -> set:
    """Load already sent tweet IDs from file"""
    sent_tweets = set()
    if os.path.exists(SENT_TWEETS_FILE):
        try:
            with open(SENT_TWEETS_FILE, 'r') as f:
                for line in f:
                    tweet_id = line.strip()
                    if tweet_id:
                        sent_tweets.add(tweet_id)
            print(f"Loaded {len(sent_tweets)} previously sent tweet IDs.")
        except Exception as e:
            print(f"Error reading sent tweets file: {e}")
    else:
        print("No previous sent tweets file found. Starting fresh.")
    return sent_tweets

def save_sent_tweet(tweet_id: str):
    """Save tweet ID to file"""
    try:
        with open(SENT_TWEETS_FILE, 'a') as f:
            f.write(f"{tweet_id}\n")
    except Exception as e:
        print(f"Error saving tweet ID: {e}")

def cleanup_old_sent_tweets(sent_tweets: set, days_to_keep: int = 7):
    """Clean up old tweet IDs to prevent file bloat"""
    try:
        if len(sent_tweets) > 10000:
            sorted_tweets = sorted(sent_tweets, key=lambda x: int(x) if x.isdigit() else 0)
            sent_tweets_to_keep = set(sorted_tweets[-8000:])
            
            with open(SENT_TWEETS_FILE, 'w') as f:
                for tweet_id in sent_tweets_to_keep:
                    f.write(f"{tweet_id}\n")
            
            print(f"Cleaned up old tweet IDs. Kept {len(sent_tweets_to_keep)} recent ones.")
            return sent_tweets_to_keep
    except Exception as e:
        print(f"Error during cleanup: {e}")
    
    return sent_tweets

async def get_best_media_url(media_item):
    """Get best quality media URL from item"""
    possible_urls = []
    
    # Check different URL attributes
    for attr in ['url', 'media_url_https', 'media_url', 'preview_image_url', 'video_url']:
        url = getattr(media_item, attr, None)
        if url and isinstance(url, str) and url.startswith(('http://', 'https://')):
            possible_urls.append(url)
    
    # Also check if it's a dict-like object
    if hasattr(media_item, '__dict__'):
        for key, value in media_item.__dict__.items():
            if 'url' in key.lower() and isinstance(value, str) and value.startswith(('http://', 'https://')):
                if value not in possible_urls:
                    possible_urls.append(value)
    
    # Return first working URL
    for url in possible_urls:
        if await validate_media_url(url):
            return url
    
    # If validation fails, return the first URL anyway (Telegram might handle it)
    return possible_urls[0] if possible_urls else None

def validate_configuration():
    """Validate configuration before starting"""
    errors = []
    
    if not X_ACCOUNTS or len(X_ACCOUNTS) == 0:
        errors.append("No Twitter accounts configured. Please add at least one account to X_ACCOUNTS.")
    else:
        for i, acc in enumerate(X_ACCOUNTS):
            if acc.get("username") == "YOUR_TWITTER_USERNAME" or not acc.get("username"):
                errors.append(f"Account #{i+1}: Username not configured")
            if acc.get("password") == "YOUR_TWITTER_PASSWORD" or not acc.get("password"):
                errors.append(f"Account #{i+1}: Password not configured")
            if acc.get("email") == "YOUR_EMAIL@example.com" or not acc.get("email"):
                errors.append(f"Account #{i+1}: Email not configured")
            if acc.get("email_password") == "YOUR_EMAIL_PASSWORD" or not acc.get("email_password"):
                errors.append(f"Account #{i+1}: Email password not configured")
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        errors.append("Telegram bot token not configured")
    
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
        errors.append("Telegram chat ID not configured")
    
    if errors:
        print("=" * 60)
        print("CONFIGURATION ERRORS:")
        print("=" * 60)
        for error in errors:
            print(f"  ❌ {error}")
        print("=" * 60)
        print("\nPlease update the configuration in scrape.py before running.")
        return False
    
    return True

async def scrape_viral_tweets():
    """Main function - initialize API and start monitoring"""
    # Validate configuration first
    if not validate_configuration():
        return
    
    set_log_level("INFO")
    api = API()
    sent_tweets = load_sent_tweets()
    sent_tweets = cleanup_old_sent_tweets(sent_tweets)

    print("--- Adding X Accounts ---")
    accounts_added = 0
    try:
        for i, acc in enumerate(X_ACCOUNTS):
            try:
                cookies = None
                if "cookies" in acc and acc["cookies"]:
                    # Parse cookies if it's a string, otherwise use as-is
                    if isinstance(acc["cookies"], str):
                        try:
                            cookies = json.loads(acc["cookies"])
                        except json.JSONDecodeError:
                            print(f"Warning: Invalid cookies format for account {i+1}, ignoring cookies")
                            cookies = None
                    else:
                        cookies = acc["cookies"]
                
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
                print(f"  ✓ Added account: {acc['username']}")
            except Exception as e:
                print(f"  ✗ Failed to add account {i+1} ({acc.get('username', 'unknown')}): {e}")
                continue
        
        if accounts_added == 0:
            print("ERROR: No accounts were successfully added. Cannot continue.")
            return
        
        print(f"Successfully added {accounts_added}/{len(X_ACCOUNTS)} account(s).")
    except Exception as e:
        print(f"Error adding accounts: {e}")
        import traceback
        traceback.print_exc()
        return

    print("--- Logging in Accounts ---")
    try:
        await api.pool.login_all()
        print("All accounts logged in successfully.")
        
        # Wait a moment for accounts to become active
        print("Waiting for accounts to become active...")
        await asyncio.sleep(2)
        
        # Verify accounts are active (with error handling)
        try:
            if hasattr(api.pool, 'accounts'):
                active_count = len([acc for acc in api.pool.accounts if hasattr(acc, 'is_active') and acc.is_active])
                if active_count > 0:
                    print(f"✓ {active_count} account(s) are active and ready")
                else:
                    print("⚠️  Warning: No active accounts detected, but continuing anyway...")
            else:
                print("✓ Accounts logged in (status check unavailable)")
        except Exception as e:
            print(f"⚠️  Could not check account status: {e}")
            print("   Continuing anyway - accounts should still work...")
    except Exception as e:
        error_str = str(e)
        print(f"Error during login: {e}")
        
        # Check for Cloudflare block
        if "403" in error_str or "Cloudflare" in error_str or "blocked" in error_str.lower():
            print("\n" + "="*60)
            print("⚠️  CLOUDFLARE BLOCK DETECTED")
            print("="*60)
            print("\nTwitter/X is blocking automated login attempts.")
            print("SOLUTION: Use cookies from an existing browser session.")
            print("\nQuick fix:")
            print("1. Open Twitter/X in your browser (make sure you're logged in)")
            print("2. Press F12 → Application tab → Cookies → https://x.com")
            print("3. Copy 'auth_token' and 'ct0' values")
            print("4. Add to scrape.py:")
            print('   "cookies": \'{"ct0": "YOUR_CT0", "auth_token": "YOUR_AUTH_TOKEN"}\'')
            print("\nSee GET_COOKIES.md for detailed instructions.")
            print("="*60)
        else:
            import traceback
            traceback.print_exc()
            print("\nTroubleshooting tips:")
            print("  - Verify your Twitter credentials are correct")
            print("  - Check if 2FA is enabled (may require additional setup)")
            print("  - Try using cookies from an existing session")
        return

    cycle_count = 0
    total_tweets_sent = 0
    
    if CONTINUOUS_MONITORING:
        print(f"\nStarting continuous monitoring (checking every {CHECK_INTERVAL_MINUTES} minutes)")
        print("Press Ctrl+C to stop")
    
    try:
        while True:
            cycle_count += 1
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n{'='*60}")
            print(f"MONITORING CYCLE #{cycle_count} - {current_time}")
            print(f"{'='*60}")
            
            new_tweets_found = await perform_scraping_cycle(api, sent_tweets)
            total_tweets_sent += new_tweets_found
            
            print(f"\nCycle #{cycle_count} Summary:")
            print(f"   New tweets sent: {new_tweets_found}")
            print(f"   Total tweets sent: {total_tweets_sent}")
            print(f"   Unique tweets tracked: {len(sent_tweets)}")
            
            if not CONTINUOUS_MONITORING:
                break
            
            print(f"\nWaiting {CHECK_INTERVAL_MINUTES} minutes before next check...")
            print(f"   Next check at: {(datetime.now() + timedelta(minutes=CHECK_INTERVAL_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')}")
            
            await asyncio.sleep(CHECK_INTERVAL_MINUTES * 60)
            
    except KeyboardInterrupt:
        print(f"\n\nMonitoring stopped by user")
        print(f"Final Statistics:")
        print(f"   Total cycles: {cycle_count}")
        print(f"   Total tweets sent: {total_tweets_sent}")
        print(f"   Unique tweets tracked: {len(sent_tweets)}")
    except Exception as e:
        print(f"\nError during monitoring: {e}")

async def perform_scraping_cycle(api, sent_tweets):
    """Perform one scraping cycle"""
    since_date = (datetime.now() - timedelta(days=MAX_AGE_DAYS)).strftime("%Y-%m-%d")
    
    # Build query - use min_faves for minimum likes
    base_query = f"min_faves:{MIN_LIKES}"
    
    # Add date filter if needed
    if MAX_AGE_DAYS > 0:
        base_query = f"{base_query} since:{since_date}"
    
    if TWEET_TYPES == "media_only":
        query = f"{base_query} filter:media"
        query_description = "media tweets only (images, videos, GIFs)"
    elif TWEET_TYPES == "text_only":
        query = f"{base_query} -filter:media"
        query_description = "text-only tweets (no media)"
    else:
        query = base_query
        query_description = "all tweets (both media and text-only)"

    print(f"Searching for viral tweets ({query_description})")
    print(f"   Query: '{query}'")
    print(f"   Minimum likes: {MIN_LIKES:,}")
    print(f"   Date range: Last {MAX_AGE_DAYS} day(s)")

    tweet_count = 0
    new_tweets_sent = 0
    duplicates_skipped = 0
    tweets_found = False
    
    # Check if we have active accounts
    try:
        if hasattr(api.pool, 'accounts'):
            active_accounts = [acc for acc in api.pool.accounts if hasattr(acc, 'is_active') and acc.is_active]
            if not active_accounts:
                print("⚠️  No active accounts detected. Attempting to refresh...")
                await asyncio.sleep(1)
                # Try to get an account for the queue
                try:
                    account = await asyncio.wait_for(api.pool.get_for_queue_or_wait(), timeout=5.0)
                    if account:
                        print(f"✓ Account available: {account.username if hasattr(account, 'username') else 'unknown'}")
                except asyncio.TimeoutError:
                    print("⚠️  Timeout waiting for account. Continuing anyway...")
                except Exception as e:
                    print(f"⚠️  Could not get active account: {e}")
                    print("   Continuing anyway - search might still work...")
            else:
                print(f"✓ {len(active_accounts)} account(s) ready for search")
    except Exception as e:
        print(f"⚠️  Warning checking account status: {e}")
        print("   Continuing with search anyway...")
    
    try:
        print("Starting search...")
        
        # Retry logic for search
        max_retries = 3
        retry_count = 0
        search_success = False
        
        while retry_count < max_retries and not search_success:
            try:
                # Try to initialize search
                search_iter = api.search(query, limit=50)
                search_success = True
                print("✓ Search initialized successfully")
            except Exception as search_init_error:
                retry_count += 1
                error_str = str(search_init_error)
                if "No active accounts" in error_str or "get_for_queue_or_wait" in error_str or "Stopping" in error_str:
                    if retry_count < max_retries:
                        wait_time = retry_count * 2
                        print(f"⚠️  Account not ready (attempt {retry_count}/{max_retries}). Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        # Try to refresh account status
                        try:
                            if hasattr(api.pool, 'login_all'):
                                print("   Attempting to refresh account status...")
                                await asyncio.sleep(1)
                        except:
                            pass
                        continue
                    else:
                        print(f"❌ Failed to get active account after {max_retries} attempts")
                        print("   The account may need cookies for better authentication.")
                        print("   Will retry on next monitoring cycle.")
                        return 0
                else:
                    # For other errors, log and try once more
                    if retry_count < max_retries:
                        print(f"⚠️  Search error (attempt {retry_count}/{max_retries}): {error_str[:100]}")
                        await asyncio.sleep(2)
                        continue
                    else:
                        raise  # Re-raise on final attempt
        
        if not search_success:
            print("❌ Could not initialize search")
            return 0
        
        # Process tweets from search
        try:
            async for tweet in search_iter:
                tweets_found = True
                try:
                tweet_count += 1
                
                # Safely get tweet ID
                tweet_id = getattr(tweet, 'id', None)
                if not tweet_id:
                    print("Skipping tweet with no ID")
                    continue
                
                tweet_id_str = str(tweet_id)
                
                if tweet_id_str in sent_tweets:
                    duplicates_skipped += 1
                    if tweet_count % 10 == 0:  # Only print every 10th duplicate to reduce spam
                        print(f"Skipping duplicate tweet ID: {tweet_id}")
                    continue
                
                # Safely get tweet attributes
                username = getattr(getattr(tweet, 'user', None), 'username', 'unknown')
                displayname = getattr(getattr(tweet, 'user', None), 'displayname', 'Unknown')
                like_count = getattr(tweet, 'likeCount', 0) or 0
                retweet_count = getattr(tweet, 'retweetCount', 0) or 0
                reply_count = getattr(tweet, 'replyCount', 0) or 0
                tweet_date = getattr(tweet, 'date', 'Unknown')
                raw_content = getattr(tweet, 'rawContent', '') or ''
                
                print(f"\nNew Tweet Found")
                print(f"   ID: {tweet_id}")
                print(f"   Author: @{username} ({displayname})")
                print(f"   Likes: {like_count:,} | Retweets: {retweet_count:,} | Replies: {reply_count:,}")
                print(f"   Date: {tweet_date}")
                print(f"   Text: {raw_content[:100]}{'...' if len(raw_content) > 100 else ''}")

                # Prepare content
                tweet_content_display = ""
                if raw_content:
                    if (raw_content.strip().startswith("http://") or 
                        raw_content.strip().startswith("https://")):
                        tweet_content_display = create_safe_url_link(raw_content.strip(), "Tweet Link")
                    else:
                        tweet_content_display = escape_markdown_v2(raw_content)
                else:
                    tweet_content_display = "*No text content*"

                tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
                tweet_link = create_safe_url_link(tweet_url, "View on X")

                telegram_message = f"""*VIRAL TWEET ALERT*

*Author*: @{escape_markdown_v2(username)} \\({escape_markdown_v2(displayname)}\\)
*Tweet ID*: `{escape_markdown_v2(str(tweet_id))}`
*Likes*: `{escape_markdown_v2(str(like_count))}`
*Retweets*: `{escape_markdown_v2(str(retweet_count))}`
*Replies*: `{escape_markdown_v2(str(reply_count))}`
*Date*: `{escape_markdown_v2(str(tweet_date))}`

*Content*:
{tweet_content_display}

{tweet_link}"""

                # Handle media
                media_items = None
                if hasattr(tweet, 'media') and tweet.media:
                    print("   Processing media...")
                    try:
                        media_items = tweet.media if isinstance(tweet.media, list) else [tweet.media]
                        
                        for i, media_item in enumerate(media_items):
                            media_type = getattr(media_item, 'type', 'unknown')
                            media_url = await get_best_media_url(media_item)
                            print(f"     Media {i+1}: Type={media_type}, URL={'Valid' if media_url else 'Invalid'}")
                    except Exception as e:
                        print(f"     Error processing media: {e}")
                        media_items = None

                # Send to Telegram
                if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                    print(f"Sending tweet {tweet_id} to Telegram...")
                    success = await send_telegram_message_with_media(
                        TELEGRAM_CHAT_ID, 
                        telegram_message, 
                        TELEGRAM_BOT_TOKEN,
                        media_items
                    )
                    
                    if success:
                        print("Successfully sent to Telegram")
                        sent_tweets.add(tweet_id_str)
                        save_sent_tweet(tweet_id_str)
                        new_tweets_sent += 1
                    else:
                        print("Failed to send to Telegram")
                    
                    print("Waiting 10 seconds before next tweet...")
                    await asyncio.sleep(10)
                else:
                    print("Telegram credentials not configured")
                    
            except Exception as e:
                print(f"Error processing tweet: {e}")
                import traceback
                traceback.print_exc()
                continue

    except Exception as e:
        error_str = str(e)
        if "No active accounts" in error_str or "get_for_queue_or_wait" in error_str:
            print(f"\n⚠️  Account activation issue: {error_str}")
            print("   This usually means the account needs more time to activate.")
            print("   Solutions:")
            print("   1. Wait a moment and the next cycle will retry")
            print("   2. Add cookies from browser for better authentication (see CLOUDFLARE_FIX.md)")
            print("   3. The scraper will automatically retry on the next cycle")
        else:
            print(f"Error during scraping cycle: {e}")
            import traceback
            traceback.print_exc()
    
    if not tweets_found and tweet_count == 0:
        print("\nNo tweets found matching the search criteria.")
        print("   This could mean:")
        print("   - No tweets match your criteria (too restrictive)")
        print("   - Account needs more time to activate")
        print("   - Search query needs adjustment")
        print(f"\n   Try:")
        print(f"   - Lowering MIN_LIKES threshold (currently: {MIN_LIKES:,})")
        print(f"   - Increasing MAX_AGE_DAYS (currently: {MAX_AGE_DAYS})")
        print(f"   - Changing TWEET_TYPES to 'all' (currently: {TWEET_TYPES})")

    print(f"\nCycle Results:")
    print(f"   Total tweets found: {tweet_count}")
    print(f"   New tweets sent: {new_tweets_sent}")
    print(f"   Duplicates skipped: {duplicates_skipped}")
    
    return new_tweets_sent

if __name__ == "__main__":
    asyncio.run(scrape_viral_tweets())