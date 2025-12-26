# How to Get Twitter Cookies (Fix Cloudflare Block)

## Why You Need Cookies

Twitter/X uses Cloudflare protection that blocks automated logins. Using cookies from an existing browser session bypasses this.

## Method 1: Chrome/Edge (Easiest)

1. **Open Twitter/X in your browser**
   - Go to https://x.com (or twitter.com)
   - Make sure you're logged in

2. **Open Developer Tools**
   - Press `F12` or right-click → "Inspect"
   - Go to the **Application** tab (Chrome) or **Storage** tab (Firefox)

3. **Get Cookies**
   - In the left sidebar, expand **Cookies**
   - Click on `https://x.com` (or `https://twitter.com`)
   - Find these cookies:
     - `auth_token` - Copy the value
     - `ct0` - Copy the value

4. **Add to scrape.py**
   ```python
   X_ACCOUNTS = [
       {
           "username": "jordanbania",
           "password": "8k7m1lqanyl0",
           "email": "haroldthompson@epithic.com",
           "email_password": "pfzwjoqgS9302",
           "cookies": '{"ct0": "YOUR_CT0_VALUE", "auth_token": "YOUR_AUTH_TOKEN_VALUE"}'
       },
   ]
   ```

## Method 2: Using Browser Extension

1. Install a cookie export extension (like "Cookie-Editor" or "EditThisCookie")
2. Export cookies for x.com
3. Find `auth_token` and `ct0` values
4. Add them to scrape.py as shown above

## Method 3: Using Python Script

Run the provided `get_cookies.py` script (if available) to extract cookies automatically.

## Quick Steps:

1. **Log in to Twitter/X in your browser** (Chrome/Edge/Firefox)
2. **Open Developer Tools** (F12)
3. **Go to Application/Storage tab**
4. **Click Cookies → https://x.com**
5. **Copy these values:**
   - `auth_token` (long string)
   - `ct0` (shorter string)
6. **Update scrape.py:**
   ```python
   "cookies": '{"ct0": "paste_ct0_here", "auth_token": "paste_auth_token_here"}'
   ```

## Example:

If your cookies are:
- `ct0`: `abc123def456`
- `auth_token`: `xyz789uvw012`

Then in scrape.py:
```python
"cookies": '{"ct0": "abc123def456", "auth_token": "xyz789uvw012"}'
```

## Important Notes:

- Cookies expire after some time (usually days/weeks)
- If login fails, get fresh cookies
- Keep cookies secure - don't share them
- Cookies are account-specific

## After Adding Cookies:

1. Save scrape.py
2. Run: `python scrape.py`
3. The scraper should now bypass Cloudflare


