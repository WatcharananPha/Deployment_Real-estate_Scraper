# Deployment Folder Index

Welcome! This folder contains everything needed to deploy the Real-Estate Scraper.

## 🚀 Quick Start (Choose One)

### For Local Development (Recommended First)
1. **Read**: `../QUICKSTART.md` (in parent directory)
2. **Edit**: `.env` file with your Facebook credentials
3. **Run**: `docker-compose up -d`
4. **Access**: http://localhost:8888

### For Azure Cloud Production
1. **Read**: `../AZURE_DEPLOYMENT.md` (in parent directory)
2. **Setup**: Azure resources (follow steps 1-3)
3. **Build**: Docker image locally
4. **Push**: To Azure Container Registry
5. **Deploy**: To Container Apps (steps 4-6)

### For Pre-Deployment Verification
1. **Run**: Full checklist in `../DEPLOYMENT_CHECKLIST.md`
2. **Verify**: All systems operational
3. **Sign-off**: Ready for production

---

## 📁 This Folder Contents

### Core Files (4 files)

**Dockerfile**
- Python 3.11 slim base image
- Installs Chrome, Selenium, and all dependencies
- Exposes port 8888 for Jupyter Lab
- Default command: Start Jupyter Lab
- Can be overridden to run individual scrapers

**docker-compose.yml**
- Orchestration for local development
- Maps ports and volumes
- Loads environment from .env
- Makes development easy with hot-reload

**requirements.txt**
- All Python dependencies with versions pinned
- 9 packages: jupyterlab, selenium, pandas, numpy, undetected-chromedriver, etc.
- Installed during Docker build

**.env**
- ⚠️ **IMPORTANT: DO NOT COMMIT THIS FILE**
- Template for credentials
- FACEBOOK_EMAIL and FACEBOOK_PASSWORD
- Already added to .gitignore
- Keep local only

---

## 🎓 Documentation (in Parent Directory)

All documentation is in the project root for easy access:

| File | Purpose | Read When |
|------|---------|-----------|
| `../QUICKSTART.md` | Get started fast | First time using |
| `../AZURE_DEPLOYMENT.md` | Deploy to Azure | Going to production |
| `../DEPLOYMENT_CHECKLIST.md` | Verify readiness | Before deploying |
| `../README_DEPLOYMENT.md` | Complete overview | Need full context |

---

## ⚡ Common Commands

### Build Docker Image
```bash
cd ..
docker build -f deployment/Dockerfile -t realestate-scraper .
```

### Start Container
```bash
docker-compose up -d
```

### Run a Scraper
```bash
docker-compose exec app python run.py facebook_urls
```

### View Logs
```bash
docker-compose logs -f app
```

### Stop Container
```bash
docker-compose down
```

---

## 🔐 Security Important

✅ `.env` is in `.gitignore` - never will be committed
✅ No credentials in Dockerfile
✅ Environment variables only
✅ Azure Key Vault ready for production

⚠️ Before committing, verify no `.env` in git:
```bash
git status  # Should NOT show deployment/.env
```

---

## 📊 Project Structure

```
deployment/          ← You are here
├── Dockerfile       ← Container image definition
├── docker-compose.yml  ← Local dev orchestration
├── requirements.txt ← Python dependencies
├── .env             ← Credentials (local only)
└── README.md        ← This file

../
├── QUICKSTART.md              ← Start here ⭐
├── AZURE_DEPLOYMENT.md        ← For Azure production
├── DEPLOYMENT_CHECKLIST.md    ← Pre-deploy verification
├── README_DEPLOYMENT.md       ← Full package overview
├── run.py                     ← CLI orchestrator
├── src/                       ← Scraper scripts
└── data/                      ← Output CSVs
```

---

## ✅ Setup Checklist

Before first use, complete:

- [ ] Edit `.env` with Facebook credentials
- [ ] Verify Docker is installed and running
- [ ] Read `../QUICKSTART.md`
- [ ] Run `docker-compose up -d`
- [ ] Access http://localhost:8888
- [ ] Test one scraper: `docker-compose exec app python run.py facebook_urls`
- [ ] Check `../data/` folder for output CSV

---

## 🆘 Troubleshooting

**Docker won't start?**
→ See `../QUICKSTART.md` → Troubleshooting

**Chrome crashes?**
→ See `../QUICKSTART.md` → "Chrome crashes in container"

**Credentials not working?**
→ See `../QUICKSTART.md` → "Credentials not working"

**Need Azure help?**
→ See `../AZURE_DEPLOYMENT.md` → Troubleshooting

**Pre-deploy verification?**
→ Use `../DEPLOYMENT_CHECKLIST.md`

---

## 📞 Next Steps

1. ✅ Edit `.env` with credentials
2. ✅ Run: `docker-compose up -d`
3. ✅ Visit: http://localhost:8888
4. ✅ Test: `python run.py facebook_urls`
5. ✅ Read: Full guides in parent directory

---

**Start with**: `../QUICKSTART.md` ⭐

Version 1.0 | November 2025 | Production Ready ✅
