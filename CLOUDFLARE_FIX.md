# Fix Cloudflare Block Issue

## Problem

You're seeing this error:
```
403 - Cloudflare block
Sorry, you have been blocked
```

This happens because Twitter/X uses Cloudflare protection that blocks automated login attempts.

## Solution: Use Browser Cookies

The best solution is to use cookies from an existing browser session where you're already logged in.

## Quick Fix (5 minutes)

### Step 1: Get Cookies from Browser

1. **Open Twitter/X in Chrome/Edge**
   - Make sure you're logged in
   - Go to https://x.com

2. **Open Developer Tools**
   - Press `F12`
   - Click the **Application** tab (or **Storage** in Firefox)

3. **Find Cookies**
   - In left sidebar: **Cookies** → **https://x.com**
   - Look for these two cookies:
     - `auth_token` (long string, starts with numbers/letters)
     - `ct0` (shorter string)

4. **Copy the Values**
   - Right-click `auth_token` → Copy value
   - Right-click `ct0` → Copy value

### Step 2: Update scrape.py

Open `scrape.py` and find the `X_ACCOUNTS` section. Add the cookies:

```python
X_ACCOUNTS = [
    {
        "username": "jordanbania",
        "password": "8k7m1lqanyl0",
        "email": "haroldthompson@epithic.com",
        "email_password": "pfzwjoqgS9302",
        "cookies": '{"ct0": "PASTE_YOUR_CT0_HERE", "auth_token": "PASTE_YOUR_AUTH_TOKEN_HERE"}'
    },
]
```

**Example:**
If your cookies are:
- `ct0`: `abc123def456ghi789`
- `auth_token`: `1234567890-ABCDEFGHIJKLMNOPQRSTUVWXYZ`

Then:
```python
"cookies": '{"ct0": "abc123def456ghi789", "auth_token": "1234567890-ABCDEFGHIJKLMNOPQRSTUVWXYZ"}'
```

### Step 3: Test Again

```bash
python scrape.py
```

It should now work! ✅

## Alternative: Use Cookie Extractor Script

You can also try the automated script:

```bash
python get_cookies.py
```

This will try to extract cookies automatically from your browser.

## Important Notes

- **Cookies expire**: They last for days/weeks. If login fails later, get fresh cookies.
- **Keep cookies secure**: Don't share them publicly.
- **One account per cookie set**: Each Twitter account has unique cookies.

## Still Having Issues?

1. Make sure you're logged into Twitter in your browser first
2. Get fresh cookies (old ones might be expired)
3. Check that the cookie format is correct (JSON string)
4. Try logging out and back into Twitter, then get new cookies

## Why This Works

When you log in via browser, Twitter sets cookies that prove you're a real user. Using these cookies in the scraper makes Twitter think it's your browser, bypassing Cloudflare protection.


