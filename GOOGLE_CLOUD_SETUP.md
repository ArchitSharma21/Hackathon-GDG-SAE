# Google Cloud Setup Guide - Airport Navigation Assistant

Complete step-by-step guide to set up Google Cloud credentials for Speech-to-Text and Text-to-Speech APIs.

---

## Prerequisites

- Google Account (Gmail)
- Credit card (for Google Cloud - but we'll stay in FREE tier)
- 15 minutes of your time

---

## STEP 1: Create Google Cloud Project

### 1.1 Go to Google Cloud Console

Open in your browser: **https://console.cloud.google.com/**

### 1.2 Accept Terms (First Time Only)

If this is your first time:
- Accept Google Cloud Terms of Service
- Choose your country
- Click "Agree and Continue"

### 1.3 Create New Project

1. Click the project dropdown at the top (says "Select a project")
2. Click "NEW PROJECT" button
3. Fill in:
   ```
   Project name: airport-navigation
   Organization: No organization
   Location: No organization
   ```
4. Click "CREATE"
5. Wait 30 seconds for project to be created

### 1.4 Note Your Project ID

After creation, you'll see:
```
Project name: airport-navigation
Project ID: airport-navigation-XXXXXX
```

**📝 WRITE DOWN YOUR PROJECT_ID** - You'll need it later!

---

## STEP 2: Enable Required APIs

### 2.1 Enable Cloud Speech-to-Text API

1. Go to: **https://console.cloud.google.com/apis/library/speech.googleapis.com**
2. Make sure your project is selected (top bar)
3. Click **"ENABLE"** button
4. Wait for API to enable (~10 seconds)

### 2.2 Enable Cloud Text-to-Speech API

1. Go to: **https://console.cloud.google.com/apis/library/texttospeech.googleapis.com**
2. Make sure your project is selected (top bar)
3. Click **"ENABLE"** button
4. Wait for API to enable (~10 seconds)

### 2.3 Verify APIs are Enabled

1. Go to: **https://console.cloud.google.com/apis/dashboard**
2. You should see:
   - ✅ Cloud Speech-to-Text API
   - ✅ Cloud Text-to-Speech API

---

## STEP 3: Create Service Account

### 3.1 Go to Service Accounts

1. Open: **https://console.cloud.google.com/iam-admin/serviceaccounts**
2. Make sure your project is selected (top bar)

### 3.2 Create Service Account

1. Click **"+ CREATE SERVICE ACCOUNT"** at the top
2. Fill in:
   ```
   Service account name: airport-nav-sa
   Service account ID: airport-nav-sa (auto-filled)
   Description: Service account for Airport Navigation Assistant
   ```
3. Click **"CREATE AND CONTINUE"**

### 3.3 Grant Permissions (Roles)

**Role 1: Cloud Speech Client**
1. In "Select a role" dropdown, search for: `Cloud Speech Client`
2. Select: **Cloud Speech > Cloud Speech Client**
3. Click **"+ ADD ANOTHER ROLE"**

**Role 2: Cloud Text-to-Speech Client**
1. In the new role dropdown, search for: `Cloud Text-to-Speech Client`
2. Select: **Cloud Text-to-Speech > Cloud Text-to-Speech Client**
3. Click **"CONTINUE"**

### 3.4 Skip Optional Settings

1. "Grant users access to this service account" - **Leave empty**
2. Click **"DONE"**

---

## STEP 4: Create and Download JSON Key

### 4.1 Find Your Service Account

1. You should now see your service account in the list:
   ```
   airport-nav-sa@airport-navigation-XXXXXX.iam.gserviceaccount.com
   ```

### 4.2 Create Key

1. Click on the service account email (the line itself, not checkbox)
2. Click on **"KEYS"** tab at the top
3. Click **"ADD KEY"** dropdown
4. Select **"Create new key"**

### 4.3 Download JSON Key

1. Choose key type: **JSON** (should be selected by default)
2. Click **"CREATE"**
3. A JSON file will download automatically:
   ```
   airport-navigation-XXXXXX-abc123def456.json
   ```

### 4.4 Save the Key File Safely

**⚠️ IMPORTANT:** This file contains sensitive credentials!

1. Move the downloaded JSON file to your project:
   ```bash
   mv ~/Downloads/airport-navigation-*.json /Users/ivanmardini/Hackathon-GDG-SAE/google-credentials.json
   ```

2. **Never commit this file to git!** (already in .gitignore)

---

## STEP 5: Configure Your Application

### 5.1 Update .env File

Open your `.env` file and update:

```bash
# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/Users/ivanmardini/Hackathon-GDG-SAE/google-credentials.json
GOOGLE_CLOUD_PROJECT_ID=airport-navigation-XXXXXX

# Lufthansa API (optional, using mock data)
LUFTHANSA_CLIENT_ID=your-client-id
LUFTHANSA_CLIENT_SECRET=your-client-secret

# App Configuration
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
```

Replace `airport-navigation-XXXXXX` with your actual PROJECT_ID!

### 5.2 Verify File Exists

```bash
ls -lh /Users/ivanmardini/Hackathon-GDG-SAE/google-credentials.json
```

Should show the file with size ~2-3 KB

---

## STEP 6: Test the Setup

### 6.1 Restart Your Server

```bash
# Kill existing server
lsof -ti:8000 | xargs kill -9

# Restart with new credentials
cd /Users/ivanmardini/Hackathon-GDG-SAE
source venv/bin/activate
cd backend
python main.py
```

### 6.2 Test Speech-to-Text

Create a test audio file or use an existing one:

```bash
# Test with a simple request
curl -X POST http://localhost:8000/api/speech/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello from Hamburg Airport","language":"en-US"}' \
  -o test-voice.mp3

# Play the result
open test-voice.mp3
```

### 6.3 Test Text-to-Speech

If you hear the voice saying "Hello from Hamburg Airport", it works! ✅

---

## STEP 7: Choose Voice Settings (Optional)

### Available Voices

You can customize the voice in `backend/services/google_speech.py`:

**English Voices:**
- `en-US-Neural2-A` - Male, natural
- `en-US-Neural2-C` - Female, natural
- `en-US-Neural2-F` - Female, warm
- `en-US-Neural2-J` - Male, professional
- `en-US-Wavenet-D` - Male, high quality
- `en-US-Wavenet-F` - Female, high quality

**German Voices (for Hamburg!):**
- `de-DE-Neural2-A` - Female
- `de-DE-Neural2-B` - Male
- `de-DE-Wavenet-A` - Female
- `de-DE-Wavenet-B` - Male

### Test Different Voices

```bash
# Test German voice
curl -X POST http://localhost:8000/api/speech/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Willkommen am Flughafen Hamburg","language":"de-DE"}' \
  -o test-german.mp3

open test-german.mp3
```

---

## Troubleshooting

### Error: "Could not automatically determine credentials"

**Fix:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/Users/ivanmardini/Hackathon-GDG-SAE/google-credentials.json
```

Then restart the server.

### Error: "Permission denied"

**Cause:** Service account doesn't have the right roles

**Fix:**
1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Find your service account
3. Click the 3 dots → "Manage permissions"
4. Add roles:
   - Cloud Speech Client
   - Cloud Text-to-Speech Client

### Error: "API has not been used in project before"

**Cause:** APIs not enabled

**Fix:**
1. Enable Speech-to-Text: https://console.cloud.google.com/apis/library/speech.googleapis.com
2. Enable Text-to-Speech: https://console.cloud.google.com/apis/library/texttospeech.googleapis.com

### Error: "Quota exceeded"

**Cause:** You've used up the free tier

**Fix:**
- Check usage: https://console.cloud.google.com/apis/api/speech.googleapis.com/quotas
- Free tier: 60 minutes/month for Speech-to-Text
- Free tier: 1M characters/month for Text-to-Speech
- Or upgrade to paid tier (very cheap for small usage)

---

## Cost Monitoring

### Check Your Usage

1. Go to: **https://console.cloud.google.com/billing**
2. Select your project
3. View "Reports" to see costs

### Set Budget Alert

1. Go to: **https://console.cloud.google.com/billing/budgets**
2. Click "CREATE BUDGET"
3. Set amount: $5 (or whatever you're comfortable with)
4. Set alert at 50%, 90%, 100%
5. Add your email

This way you'll get notified if you're about to exceed free tier.

---

## Security Best Practices

### ✅ DO:
- Keep the JSON key file secure
- Add `google-credentials.json` to `.gitignore` (already done)
- Use environment variables for the path
- Rotate keys every 90 days in production
- Delete unused service accounts

### ❌ DON'T:
- Commit the JSON file to git
- Share the JSON file publicly
- Hardcode credentials in code
- Use the same key for dev and production
- Leave unused APIs enabled

---

## Quick Reference Commands

```bash
# Move credentials file
mv ~/Downloads/airport-navigation-*.json /Users/ivanmardini/Hackathon-GDG-SAE/google-credentials.json

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=/Users/ivanmardini/Hackathon-GDG-SAE/google-credentials.json

# Test TTS
curl -X POST http://localhost:8000/api/speech/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Testing Google Cloud Text to Speech","language":"en-US"}' \
  -o test.mp3 && open test.mp3

# Check if credentials work
python3 -c "from google.cloud import speech_v1; print('✓ Speech API connected!')"
python3 -c "from google.cloud import texttospeech_v1; print('✓ TTS API connected!')"
```

---

## You're All Set! 🎉

Your Google Cloud credentials are now configured. The app will automatically use:
- **Google Cloud TTS** for high-quality voice output
- **Google Cloud Speech** for accurate voice recognition

Restart your server and test the APIs!

**Next steps:**
1. Update frontend to use Google TTS endpoint (optional)
2. Test with different voices
3. Monitor usage in Google Cloud Console

---

**Questions?** Check the troubleshooting section or Google Cloud documentation:
- Speech-to-Text: https://cloud.google.com/speech-to-text/docs
- Text-to-Speech: https://cloud.google.com/text-to-speech/docs
