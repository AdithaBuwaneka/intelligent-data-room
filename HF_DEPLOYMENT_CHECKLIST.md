# 🚀 Hugging Face Deployment Checklist

## ❌ What Was Broken
1. **Exit code 137** = Container Out of Memory (OOM) on HF Spaces
2. **Missing MONGODB_URI** in secrets documentation
3. **Unclear error messages** during startup failures
4. **No troubleshooting for memory issues**

## ✅ What's Fixed
1. ✅ Updated `README_HUGGINGFACE.md` to include **MONGODB_URI** in secrets
2. ✅ Added detailed troubleshooting for exit code 137 
3. ✅ Improved error messages in `main.py` startup logs
4. ✅ Added memory optimization guidance

## 🎯 To Deploy Successfully:

### Before Pushing to HF Spaces:

1. **Verify all environment variables are set:**
   - [ ] `GEMINI_API_KEY` - Google Gemini API key
   - [ ] `MONGODB_URI` - MongoDB Atlas connection string (including password!)
   - [ ] `IMAGEKIT_PRIVATE_KEY` - ImageKit credentials
   - [ ] `IMAGEKIT_PUBLIC_KEY` - ImageKit credentials
   - [ ] `IMAGEKIT_URL_ENDPOINT` - ImageKit endpoint

2. **Verify MongoDB Atlas:**
   - [ ] Connection string includes `<password>` replaced with actual password
   - [ ] Network access allows `0.0.0.0/0` (or at least HF Spaces IP)
   - [ ] Database name is included in connection string

3. **Push code:**
   ```bash
   git add README_HUGGINGFACE.md backend/app/main.py
   git commit -m "Fix: Add missing MONGODB_URI to secrets and improve error handling"
   git push hf main
   ```

4. **In HF Space Settings:**
   - Go to **Repository secrets**
   - Add all 6 secrets (GEMINI_API_KEY, MONGODB_URI, ImageKit keys, ALLOWED_ORIGINS)
   - Space will auto-rebuild

5. **Monitor the build:**
   - Check **Logs** tab
   - Should see: "✅ Connected to MongoDB Atlas" + "✅ Application started successfully"
   - Then should show: "Uvicorn running on http://0.0.0.0:7860"

6. **Test the endpoint:**
   ```bash
   curl https://YOUR_USERNAME-intelligent-data-room.hf.space/health
   ```
   Should return: `{"status": "healthy", "version": "1.0.0", "service": "intelligent-data-room-api"}`

## 🔍 If Still Having Issues:

### Exit code 137 (OOM):
- Reduce `MAX_CONTEXT_MESSAGES` to 3 in secrets
- Check MongoDB connection string is valid
- Verify no secret values are missing or invalid

### Application won't start:
- Check **Logs** tab for specific error
- Look for line mentioning missing env vars
- Verify MONGODB_URI format: `mongodb+srv://user:password@cluster.mongodb.net/database?retryWrites=true&w=majority`

### Health check fails:
- Wait 30 seconds after Space starts (startup takes time)
- Check CORS settings: `ALLOWED_ORIGINS=*` for testing
- Factory reboot Space if stuck: Settings → "Factory reboot"

## 📝 Key Changes Made:
- `README_HUGGINGFACE.md`: Added MONGODB_URI to secrets + exit code 137 troubleshooting
- `backend/app/main.py`: Improved startup error messages
- This file: Deployment checklist for reference
