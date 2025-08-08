# 🔗 SingleBrief Integration Setup Guide

**Product Owner's Guide to API Configuration**

## 📍 **THE ONE FILE YOU NEED: `.env`**

All third-party API credentials go in **ONE PLACE**: `/Users/aarora/singlebrief_fullversion/.env`

Copy from `.env.example` and fill in your actual API keys, client IDs, and secrets.

---

## 🎯 **Available Integrations & Status**

| Integration | Status | API Endpoints | OAuth Flow |
|-------------|---------|---------------|------------|
| **Slack** | ✅ Ready | `/api/v1/slack/*` | ✅ Implemented |
| **Gmail** | ✅ Ready | `/api/v1/email-calendar/*` | ✅ Implemented |
| **Outlook** | ✅ Ready | `/api/v1/email-calendar/*` | ✅ Implemented |
| **Google Drive** | ✅ Ready | `/api/v1/documents/*` | ✅ Implemented |
| **OneDrive** | ✅ Ready | `/api/v1/documents/*` | ✅ Implemented |
| **GitHub** | ✅ Ready | `/api/v1/developer-tools/*` | ✅ Implemented |
| **Jira** | ✅ Ready | `/api/v1/developer-tools/*` | ✅ Implemented |
| **Teams** | 🔄 Partial | No dedicated endpoint | ❌ Needs implementation |

---

## 🔑 **Required API Credentials**

### **1. AI Services** (Required for core functionality)
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxx
```

### **2. Vector Database** (Choose one)
```bash
# Option A: Pinecone (Recommended)
VECTOR_DATABASE_TYPE=pinecone
PINECONE_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PINECONE_ENVIRONMENT=us-east1-gcp

# Option B: Weaviate (Self-hosted)
VECTOR_DATABASE_TYPE=weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-weaviate-key
```

### **3. Team Communication**
```bash
# Slack Integration
SLACK_CLIENT_ID=1234567890.1234567890
SLACK_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### **4. Google Services** (Gmail, Drive, Calendar)
```bash
GOOGLE_CLIENT_ID=123456789012-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx
```

### **5. Microsoft Services** (Outlook, OneDrive)
```bash
MICROSOFT_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MICROSOFT_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### **6. Developer Tools**
```bash
# GitHub Integration
GITHUB_CLIENT_ID=Iv1.xxxxxxxxxxxxxxxx
GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# Jira Integration
JIRA_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
JIRA_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
JIRA_WEBHOOK_SECRET=your-jira-webhook-secret
```

---

## 🚀 **Quick Setup Steps**

1. **Copy template:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in API credentials** in `.env` file

3. **Restart the application:**
   ```bash
   # Backend
   cd backend && uvicorn app.main:app --reload
   
   # Frontend  
   cd frontend && npm run dev
   ```

4. **Test integrations** via API endpoints or UI

---

## 🔧 **How to Get API Credentials**

### **Slack**
1. Go to [Slack API](https://api.slack.com/apps)
2. Create new app → "From scratch"
3. Get Client ID & Client Secret from "Basic Information"

### **Google (Gmail, Drive, Calendar)**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable APIs (Gmail, Drive, Calendar)
3. Create OAuth 2.0 credentials
4. Set redirect URI: `http://localhost:8000/api/v1/email-calendar/oauth/callback`

### **Microsoft (Outlook, OneDrive)**
1. Go to [Azure Portal](https://portal.azure.com/)
2. App registrations → New registration
3. Add redirect URI: `http://localhost:8000/api/v1/email-calendar/oauth/callback`

### **GitHub**
1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Create new OAuth app
3. Set callback URL: `http://localhost:8000/api/v1/developer-tools/oauth/callback`

### **Jira**
1. Go to [Atlassian Developer Console](https://developer.atlassian.com/)
2. Create OAuth 2.0 app
3. Set callback URL: `http://localhost:8000/api/v1/developer-tools/oauth/callback`

---

## ⚡ **Integration Workflow**

1. **Setup:** Add credentials to `.env` file
2. **OAuth:** Users authenticate via `/api/v1/{service}/oauth/initiate`
3. **Callback:** System receives tokens via `/api/v1/{service}/oauth/callback`
4. **Data Flow:** APIs automatically fetch data using stored tokens
5. **Brief Generation:** All integrated data appears in daily briefs

---

## 🛡️ **Security Features**

- ✅ OAuth tokens encrypted and stored securely
- ✅ Rate limiting implemented per integration
- ✅ GDPR compliance with data retention policies
- ✅ Webhook signature verification
- ✅ Scope-based permissions per integration

---

## 📊 **Integration Status Monitoring**

Check integration health via:
- **API:** `GET /api/v1/{service}/status`
- **Admin UI:** Integration dashboard (when implemented)
- **Logs:** Check backend logs for connection issues

---

## 🚨 **Troubleshooting**

### **Common Issues:**
1. **"Integration not found"** → Check `.env` file has correct keys
2. **"OAuth failed"** → Verify redirect URIs match exactly
3. **"Rate limit exceeded"** → Check quota limits in integration settings
4. **"Invalid credentials"** → Regenerate API keys/secrets

### **Debug Mode:**
```bash
LOG_LEVEL=DEBUG
```

---

## ✅ **Validation Checklist**

- [ ] `.env` file contains all required API keys
- [ ] OAuth redirect URIs configured correctly
- [ ] Database migrations run successfully
- [ ] Vector database accessible
- [ ] Backend server starts without errors
- [ ] Integration endpoints return 200 status
- [ ] OAuth flows complete successfully
- [ ] Data syncing works for each integration