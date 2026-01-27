# Deploy to Hugging Face Spaces 🚀

## ✅ Why Hugging Face?
- **16GB RAM** - No build memory issues!
- **Free forever** - No credit card needed
- **No auto-sleep** - Always available
- **Easy deployment** - Push and deploy
- **Community visibility** - Share your work

---

## 📋 Step-by-Step Deployment

### **Step 1: Create Hugging Face Account**
1. Go to https://huggingface.co/join
2. Sign up (free)
3. Verify your email

### **Step 2: Create New Space**
1. Go to https://huggingface.co/spaces
2. Click **"Create new Space"** button
3. Fill in details:
   - **Space name:** `intelligent-data-room`
   - **License:** MIT
   - **Space SDK:** ⚠️ **Select "Docker"** (very important!)
   - **Space hardware:** CPU basic (free)
   - **Visibility:** Public
4. Click **"Create Space"**

### **Step 3: Prepare Your Files**
In your project folder, make sure you have:
- ✅ `Dockerfile` (already created)
- ✅ `backend/` folder with all code
- ✅ `.dockerignore` (already created)

### **Step 4: Push Code to Hugging Face**

**Option A: Using Git (Recommended)**

```bash
# In your project root (d:\intelligent-data-room)

# Add HF remote (replace YOUR_USERNAME with your HF username)
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/intelligent-data-room

# Copy README for HF Space
cp README_HF_SPACE.md README.md

# Commit all files
git add Dockerfile .dockerignore backend/ README.md
git commit -m "Deploy to Hugging Face Spaces"

# Push to HF
git push hf main
```

**Option B: Using Web Interface**

1. In your Space, click "Files" tab
2. Click "Add file" → "Upload files"
3. Upload:
   - `Dockerfile`
   - `backend/` (entire folder)
   - `.dockerignore`
4. Click "Commit changes to main"

### **Step 5: Add Environment Variables (Secrets)**
1. In your Space, go to **Settings** tab
2. Scroll to **"Repository secrets"**
3. Click **"New secret"** and add each:

```
Name: GEMINI_API_KEY
Value: [your Google Gemini API key]

Name: IMAGEKIT_PRIVATE_KEY
Value: [your ImageKit private key]

Name: IMAGEKIT_PUBLIC_KEY
Value: [your ImageKit public key]

Name: IMAGEKIT_URL_ENDPOINT
Value: [your ImageKit URL endpoint]

Name: ALLOWED_ORIGINS
Value: *
```

4. Click "Save" for each secret

### **Step 6: Wait for Build**
- HF will automatically build your Docker image
- Check the **"Logs"** tab to see build progress
- Build takes ~5-10 minutes
- Status will change from "Building" → "Running"

### **Step 7: Test Your API**
Your backend will be live at:
```
https://YOUR_USERNAME-intelligent-data-room.hf.space
```

Test it:
```bash
curl https://YOUR_USERNAME-intelligent-data-room.hf.space/health
```

Should return: `{"status": "healthy"}`

### **Step 8: Deploy Frontend to Vercel**

```bash
cd frontend

# Update API URL in .env
echo "VITE_API_URL=https://YOUR_USERNAME-intelligent-data-room.hf.space" > .env.production

# Deploy
npx vercel --prod
```

When prompted:
- Set up and deploy? **Y**
- Link to existing project? **N**
- Project name? `intelligent-data-room-frontend`
- Deploy? **Y**

---

## 🔧 Troubleshooting

### Build fails?
Check logs in HF Space → "Logs" tab. Common issues:
- Missing `Dockerfile` → Make sure it's in root
- Wrong SDK → Must be "Docker" not "Gradio"
- Port issue → Must use port 7860

### API not responding?
- Check secrets are set correctly
- View logs for errors
- Restart Space: Settings → "Factory reboot"

### CORS errors from frontend?
Add to secrets:
```
ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

Or allow all (for testing):
```
ALLOWED_ORIGINS=*
```

---

## 📊 Your Final URLs

**Backend API (HF Space):**
```
https://YOUR_USERNAME-intelligent-data-room.hf.space
```

**Frontend (Vercel):**
```
https://intelligent-data-room-frontend.vercel.app
```

**Docs:**
```
https://YOUR_USERNAME-intelligent-data-room.hf.space/docs
```

---

## 🎥 For Your Video Submission

Show:
1. Your HF Space running (the URL)
2. Frontend on Vercel
3. Upload CSV and ask questions
4. Explain multi-agent system
5. Show context retention

---

## 💡 Quick Commands Reference

```bash
# Add HF remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/intelligent-data-room

# Push updates
git add .
git commit -m "Update"
git push hf main

# Check Space URL
echo "https://YOUR_USERNAME-intelligent-data-room.hf.space"

# Deploy frontend
cd frontend && npx vercel --prod
```

---

## ✅ Checklist

- [ ] Created HF account
- [ ] Created Space with **Docker SDK**
- [ ] Pushed Dockerfile and backend code
- [ ] Added all environment secrets
- [ ] Waited for build to complete
- [ ] Tested `/health` endpoint
- [ ] Deployed frontend to Vercel
- [ ] Updated frontend API URL
- [ ] Tested full app
- [ ] Recorded demo video

---

Need help? Check HF Spaces docs: https://huggingface.co/docs/hub/spaces
