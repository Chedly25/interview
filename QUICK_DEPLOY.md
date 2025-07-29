# 🚀 Quick Deployment Guide

## 🌐 Deploy Your Automotive Assistant (FREE)

### **Backend: Railway**
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. "New Project" → "Deploy from GitHub repo"
4. Select `Chedly25/interview`
5. **Add Environment Variable:**
   - Name: `ANTHROPIC_API_KEY`
   - Value: [Use the Claude API key from our chat conversation]
6. Deploy will complete automatically

### **Frontend: Vercel**
1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub  
3. "Import Project" → Select `Chedly25/interview`
4. **Root Directory:** Set to `frontend`
5. **Add Environment Variable:**
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: Your Railway URL (e.g. `https://interview-production.railway.app`)
6. Deploy!

## 🎉 Result
Your automotive website will be live with:
- ✅ French car listings interface
- ✅ AI-powered car analysis with Claude
- ✅ Price and location filters
- ✅ Modern responsive design
- ✅ Professional automotive website

**Estimated time: 5-10 minutes total**

Your sites will be accessible at:
- Frontend: `https://interview-[username].vercel.app`
- Backend: `https://interview-production.railway.app`

## 🔧 After Deployment
1. Visit your frontend URL to see the website
2. The database starts empty - you can add sample data by running `python backend/sample_data.py` in Railway's console
3. Test the Claude AI analysis on any car listing!

**No terminal commands, no complex setup - just deploy and use!** 🚗✨