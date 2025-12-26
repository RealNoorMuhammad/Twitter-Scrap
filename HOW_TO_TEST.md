# How to Check if the Scraper is Working

## Quick Test Method

### Step 1: Run the Test Script

The easiest way to check if everything is configured correctly is to run the test script:

```bash
python test_scraper.py
```

This will check:
- ✅ Configuration is valid
- ✅ Telegram bot connection works
- ✅ Twitter accounts can login
- ✅ Twitter search functionality works

### Step 2: What to Look For

**If all tests pass:**
```
✅ Configuration is valid
✅ Telegram: PASS
✅ Twitter Login: PASS
✅ Twitter Search: PASS

🎉 All critical tests passed! Your scraper should work.
```

**If tests fail:**
- The script will tell you exactly what's wrong
- Fix the issues it reports
- Run the test again

## Manual Testing Steps

### 1. Check Configuration

Make sure you've edited `scrape.py` and filled in:
- Twitter account credentials (username, password, email, email_password)
- Telegram bot token
- Telegram chat ID

### 2. Test Telegram Bot

Send a test message manually:
1. Open Telegram
2. Find your bot (the one you created with @BotFather)
3. Send it a message: `/start`
4. If the bot responds, it's working

Or use this Python one-liner:
```python
import requests
requests.post(f"https://api.telegram.org/bot{YOUR_BOT_TOKEN}/sendMessage", 
              json={"chat_id": YOUR_CHAT_ID, "text": "Test"})
```

### 3. Test Twitter Connection

The scraper will automatically test Twitter when it starts. Look for:
```
--- Adding X Accounts ---
  ✓ Added account: your_username
Successfully added 1/1 account(s).

--- Logging in Accounts ---
All accounts logged in successfully.
```

If you see errors, check:
- Username and password are correct
- Email and email password are correct
- No 2FA is enabled (or use cookies)

### 4. Run the Scraper

Once tests pass, run the main scraper:

```bash
python scrape.py
```

**What you should see:**

1. **Configuration validation:**
   ```
   --- Adding X Accounts ---
   ✓ Added account: your_username
   ```

2. **Login success:**
   ```
   --- Logging in Accounts ---
   All accounts logged in successfully.
   ```

3. **Search starting:**
   ```
   ============================================================
   MONITORING CYCLE #1 - 2024-01-01 12:00:00
   ============================================================
   Searching for viral tweets (media tweets only)
   Query: 'since:2024-01-01 min_faves:5000 filter:media'
   ```

4. **Tweets found (if any):**
   ```
   New Tweet Found
      ID: 1234567890
      Author: @username (Display Name)
      Likes: 5,234 | Retweets: 123 | Replies: 45
   ```

5. **Telegram messages:**
   - Check your Telegram channel/group
   - You should see messages with viral tweets

## Common Issues and Solutions

### ❌ "No Twitter accounts configured"
**Solution:** Edit `scrape.py` and add your Twitter account credentials to `X_ACCOUNTS`

### ❌ "Telegram bot token not configured"
**Solution:** Get your bot token from @BotFather and add it to `TELEGRAM_BOT_TOKEN`

### ❌ "Telegram chat ID not configured"
**Solution:** Get your chat ID using @userinfobot or @getidsbot

### ❌ "Failed to login"
**Solutions:**
- Check username/password are correct
- If 2FA is enabled, you may need to use cookies instead
- Try logging in manually on Twitter first

### ❌ "No tweets found"
**Solutions:**
- Lower `MIN_LIKES` (try 1000 instead of 5000)
- Increase `MAX_AGE_DAYS` (try 7 instead of 1)
- Change `TWEET_TYPES` to "all" instead of "media_only"

### ❌ "Failed to send to Telegram"
**Solutions:**
- Verify bot token is correct
- Make sure bot is added to channel/group as admin
- Check chat ID is correct (should start with `-` for groups/channels)

## Monitoring the Scraper

When the scraper is running, you'll see:

- **Cycle summaries** every 10 minutes (or your configured interval)
- **New tweets** as they're found
- **Statistics** showing total tweets sent

To stop the scraper, press `Ctrl+C`

## Expected Behavior

**First run:**
- May take a few minutes to find tweets (depending on your criteria)
- Will send all matching tweets found

**Subsequent runs:**
- Only sends new tweets (tracks duplicates)
- Faster since it skips already-sent tweets

**Continuous monitoring:**
- Checks every 10 minutes (or your configured interval)
- Sends new viral tweets as they appear
- Keeps running until you stop it

## Still Having Issues?

1. Run `python test_scraper.py` to see detailed error messages
2. Check the error output - it usually tells you exactly what's wrong
3. Make sure all dependencies are installed: `pip install -r requirements.txt`
4. Verify your credentials are correct (no typos, no extra spaces)


