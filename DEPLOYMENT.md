# Deployment Guide

## Quick Deployment Options

### Option 1: Google Cloud Run (Recommended)

#### Prerequisites
- Google Cloud account
- `gcloud` CLI installed
- Docker installed

#### Steps

1. **Prepare the Dockerfile**

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy backend
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Install dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

2. **Deploy to Cloud Run**

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
gcloud run deploy airport-nav \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT_ID=YOUR_PROJECT_ID
```

3. **Set environment variables** in Cloud Run console
   - LUFTHANSA_CLIENT_ID
   - LUFTHANSA_CLIENT_SECRET
   - GOOGLE_CLOUD_PROJECT_ID

4. **Access your app** at the provided Cloud Run URL

---

### Option 2: Render.com

#### Steps

1. **Create `render.yaml`**

```yaml
services:
  - type: web
    name: airport-nav
    env: python
    region: frankfurt
    buildCommand: pip install -r backend/requirements.txt
    startCommand: uvicorn backend.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: GOOGLE_APPLICATION_CREDENTIALS
        sync: false
      - key: LUFTHANSA_CLIENT_ID
        sync: false
      - key: LUFTHANSA_CLIENT_SECRET
        sync: false
```

2. **Connect GitHub repo** to Render

3. **Add environment variables** in Render dashboard

4. **Deploy** - Render auto-deploys on git push

---

### Option 3: Railway.app

#### Steps

1. **Install Railway CLI**
```bash
npm install -g @railway/cli
```

2. **Login and initialize**
```bash
railway login
railway init
```

3. **Set environment variables**
```bash
railway variables set LUFTHANSA_CLIENT_ID=your_id
railway variables set LUFTHANSA_CLIENT_SECRET=your_secret
```

4. **Deploy**
```bash
railway up
```

---

### Option 4: Vercel (Frontend + Serverless Backend)

#### Steps

1. **Install Vercel CLI**
```bash
npm install -g vercel
```

2. **Create `vercel.json`**

```json
{
  "builds": [
    {
      "src": "backend/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "backend/main.py"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ]
}
```

3. **Deploy**
```bash
vercel
```

---

## Environment Variables Required

```bash
# Google Cloud (Required for TTS/STT)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GOOGLE_CLOUD_PROJECT_ID=your-project-id

# Lufthansa API (Required for real flight data, optional with mock data)
LUFTHANSA_CLIENT_ID=your-client-id
LUFTHANSA_CLIENT_SECRET=your-client-secret

# App Configuration
ENVIRONMENT=production
BACKEND_URL=https://your-domain.com
```

---

## Post-Deployment Checklist

### HTTPS Configuration
- [ ] Ensure HTTPS is enabled (required for microphone access)
- [ ] Update CORS settings in `backend/main.py` with production domains
- [ ] Update PWA manifest with production URLs

### Security
- [ ] Rotate API keys if exposed in git history
- [ ] Set up rate limiting
- [ ] Enable CORS only for your domain
- [ ] Review and restrict IAM permissions

### Performance
- [ ] Enable CDN for frontend assets
- [ ] Configure caching headers
- [ ] Optimize images (icons)
- [ ] Enable gzip compression

### Monitoring
- [ ] Set up logging (Google Cloud Logging, Sentry, etc.)
- [ ] Configure error tracking
- [ ] Set up uptime monitoring
- [ ] Add analytics (Google Analytics, Plausible)

### PWA
- [ ] Test installation on iOS
- [ ] Test installation on Android
- [ ] Verify service worker caching
- [ ] Test offline functionality

---

## Custom Domain Setup

### Google Cloud Run

```bash
gcloud run services update airport-nav \
  --region us-central1 \
  --add-cloudsql-instances YOUR_INSTANCE
```

Then map domain in Cloud Run console.

### Render/Railway/Vercel

Add custom domain in the respective dashboard and follow DNS instructions.

---

## Scaling Considerations

### Database (Future Enhancement)
- Use Cloud Firestore for airport data
- Cache frequently accessed routes
- Store user preferences

### CDN
- Serve static assets from CDN (Cloudflare, Cloud CDN)
- Cache API responses appropriately

### Load Balancing
- Use cloud provider's load balancer
- Consider multi-region deployment for global users

---

## Troubleshooting

### Issue: "Module not found" errors
**Solution:** Ensure all paths are correct, use absolute imports

### Issue: Google Cloud credentials not found
**Solution:** Upload service account JSON and set env var path correctly

### Issue: CORS errors
**Solution:** Update `allow_origins` in `backend/main.py`

### Issue: PWA not installing
**Solution:** Ensure HTTPS, valid manifest.json, service worker registered

---

## Cost Estimates

### Google Cloud Run
- **Free tier:** 2 million requests/month
- **Estimated cost:** $0-10/month for moderate use
- **Speech API:** $0.006 per 15 seconds (generous free tier)

### Render
- **Free tier:** Available with limitations
- **Starter:** $7/month

### Railway
- **Free tier:** $5 credit/month
- **Hobby:** $5/month

### Vercel
- **Free tier:** Hobby use
- **Pro:** $20/month

---

## Maintenance

### Regular Updates
- Update Python dependencies monthly
- Test after cloud provider platform updates
- Review API usage and costs

### Backup
- Export airport data regularly
- Backup environment variables
- Document all configurations

---

**Deployment complete! Your app should now be live and accessible worldwide. 🌍**
