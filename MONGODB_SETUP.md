# MongoDB Atlas Setup for Hugging Face Spaces

## 🔗 Get Your MongoDB Connection String

### Step 1: Login to MongoDB Atlas
1. Go to https://www.mongodb.com/cloud/atlas
2. Sign in or create account (free tier available)
3. Click "Create" → "Build a Database"
4. Choose "M0 Sandbox" (free)
5. Select cloud provider & region
6. Click "Create Deployment"

### Step 2: Create Database User
1. In Atlas, go to **Database Access** (left sidebar)
2. Click **"Add New Database User"**
3. Set username and password (remember these!)
4. Click "Add User"

### Step 3: Get Connection String
1. Go to **Databases** (left sidebar)
2. Click **"Connect"** on your cluster
3. Select **"Drivers"** 
4. Choose **Python 3.11+**
5. Copy the connection string

Your string will look like:
```
mongodb+srv://USERNAME:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

### Step 4: Add Your Credentials
Replace `USERNAME` and `PASSWORD` with what you created in Step 2.

**Example:**
```
mongodb+srv://myuser:mypassword123@cluster0.abc123.mongodb.net/?retryWrites=true&w=majority
```

### Step 5: Add HF Spaces to Network Access
1. Go to **Network Access** (left sidebar)
2. Click **"Add IP Address"**
3. Enter: `0.0.0.0/0` (allows all IPs - for testing)
   - For production: Use specific HF Spaces IP if available
4. Click "Confirm"

⚠️ **WARNING**: `0.0.0.0/0` allows anyone with credentials to connect. In production, use IP whitelisting.

### Step 6: Add to HF Space Secrets
1. Go to your HF Space → **Settings**
2. Click **"New secret"**
3. Name: `MONGODB_URI`
4. Value: Paste your connection string from Step 3
5. Click "Save"

## ✅ Verify Connection

After deploying to HF Spaces:

1. Check logs in Space → **Logs** tab
2. Look for: `✅ Connected to MongoDB Atlas`
3. Also check: `✅ Database indexes created`

If you see errors, common issues:
- **"Connection timeout"** → IP not whitelisted in Network Access
- **"Authentication failed"** → Wrong username/password in connection string
- **"Invalid URI"** → Connection string malformed (check it starts with `mongodb+srv://`)

## 🆓 Free Tier Limits
- **Storage**: 512MB (plenty for testing)
- **Connections**: Limited but sufficient
- **No charge**: Forever free

## 🔐 Security Best Practices
1. Never commit MongoDB URI to Git (use environment variables)
2. Use strong passwords (20+ characters with numbers/symbols)
3. Whitelist specific IPs instead of `0.0.0.0/0` when possible
4. Rotate credentials periodically
