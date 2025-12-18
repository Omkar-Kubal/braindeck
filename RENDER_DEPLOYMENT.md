# 🚀 Render Deployment Guide

## Step 1: Push to GitHub

```bash
# Navigate to your project
cd d:\Flash-Card

# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Complete BrainDeck app ready for deployment"

# Create GitHub repo and add remote
# Go to github.com and create a new repository called "braindeck"
# Then run:
git remote add origin https://github.com/YOUR_USERNAME/braindeck.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy on Render

### A. Sign Up
1. Go to https://render.com
2. Sign up with GitHub

### B. Create PostgreSQL Database
1. Click "New +" → "PostgreSQL"
2. **Name:** `braindeck-db`
3. **Database:** `braindeck`
4. **User:** `braindeck`
5. **Region:** Choose closest to you
6. **Plan:** Free
7. Click "Create Database"
8. **Copy the Internal Database URL** (save for later)
dpg-d51s1rjuibrs739gu890-a

### C. Deploy Backend
1. Click "New +" → "Web Service"
2. Connect your GitHub repo
3. **Name:** `braindeck-backend`
4. **Root Directory:** Leave blank
5. **Environment:** Python 3
6. **Build Command:** `pip install -r requirements.txt`
7. **Start Command:** `gunicorn run:app`
8. **Plan:** Free

**Environment Variables:**
```
FLASK_ENV=production
SECRET_KEY=your-super-secret-random-string-change-this
GEMINI_API_KEY=your-gemini-api-key-here
DATABASE_URL=paste-internal-database-url-from-step-B
```

9. Click "Create Web Service"
10. Wait for build to complete
11. **Copy your backend URL** (e.g., `https://braindeck-backend.onrender.com`)

### D. Deploy Frontend
1. Click "New +" → "Web Service"
2. Select same GitHub repo
3. **Name:** `braindeck-frontend`
4. **Root Directory:** `frontend`
5. **Environment:** Node
6. **Build Command:** `npm install && npm run build`
7. **Start Command:** `npm start`
8. **Plan:** Free

**Environment Variables:**
```
NEXT_PUBLIC_API_URL=paste-your-backend-url-from-step-C
```

9. Click "Create Web Service"
10. Wait for deployment

---

## Step 3: Update Backend CORS

Your backend needs to allow requests from your frontend URL.

1. Go to your backend service settings
2. Add environment variable:
```
FRONTEND_URL=https://braindeck-frontend.onrender.com
```

3. Redeploy backend

---

## ✅ Done!

Your app is live at:
- **Frontend:** https://braindeck-frontend.onrender.com
- **Backend API:** https://braindeck-backend.onrender.com/api

---

## ⚠️ Free Tier Limitations

- Services spin down after 15 min of inactivity
- First request takes 30-60 seconds (cold start)
- 750 hours/month free (enough for 1 app always running)

---

## 🐛 Troubleshooting

**Backend won't start?**
- Check logs in Render dashboard
- Verify DATABASE_URL is set
- Check all environment variables

**Frontend can't reach backend?**
- Verify NEXT_PUBLIC_API_URL is correct
- Check backend CORS settings
- Look at browser console for errors

**Database errors?**
- Ensure DATABASE_URL uses `postgresql://` not `postgres://`
- Check database is running in Render dashboard
