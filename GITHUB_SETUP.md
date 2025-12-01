# GitHub Repository Setup Guide

## 📋 Repository Information

**Repository Name:** langswap-app  
**Owner:** jakemadamson2k14@gmail.com  
**Description:** Bidirectional Language Learning Platform - Thai ⇄ English

---

## 🚀 Initial Setup Commands

### 1. Initialize Git Repository (Already Done)
```bash
cd /app
git init
git branch -M main
```

### 2. Create GitHub Repository

**Option A: Using GitHub CLI**
```bash
gh auth login
gh repo create langswap-app --public --source=. --remote=origin
```

**Option B: Manual Setup**
1. Go to https://github.com/new
2. Create repository named: `langswap-app`
3. Don't initialize with README (we have one)
4. Set as Public or Private
5. Copy the repository URL

### 3. Connect Local to Remote
```bash
cd /app
git remote add origin https://github.com/YOUR_USERNAME/langswap-app.git
# Or with SSH:
# git remote add origin git@github.com:YOUR_USERNAME/langswap-app.git
```

### 4. Add All Files and Commit
```bash
git add -A
git commit -m "Initial commit: LangSwap v1.0.0 - Bilingual Learning Platform

Features:
- 350+ lessons with bidirectional learning (Thai ⇄ English)
- Speech-to-Translate with microphone permissions
- 30+ UI languages support
- Dark/Light mode with OLED optimization
- User authentication with staff/admin roles
- Progress tracking and favorites
- Text-to-Speech for all lessons
- Microphone permissions with global compliance (GDPR, CCPA, PDPA)
- Image support for lesson cards
- Comprehensive settings with app features documentation"
```

### 5. Push to GitHub
```bash
git push -u origin main
```

---

## 🔐 Authentication Setup

### Using Personal Access Token (Recommended)
1. Go to GitHub Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name: "LangSwap Repository Access"
4. Select scopes:
   - ✅ `repo` (all)
   - ✅ `workflow`
5. Generate token and copy it
6. Use token as password when pushing:
```bash
git push -u origin main
# Username: jakemadamson2k14
# Password: [your-personal-access-token]
```

### Using SSH (Alternative)
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "jakemadamson2k14@gmail.com"

# Add to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub
# Add this key to GitHub: Settings → SSH and GPG keys → New SSH key

# Test connection
ssh -T git@github.com

# Change remote to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/langswap-app.git
```

---

## 📂 Repository Structure

```
langswap-app/
├── frontend/               # Expo React Native app
│   ├── app/               # Expo Router pages
│   ├── components/        # Reusable components
│   ├── contexts/          # React contexts (Theme, Language, etc.)
│   ├── i18n/             # Internationalization
│   └── package.json
├── backend/              # FastAPI server
│   ├── server.py         # Main API
│   ├── requirements.txt  # Python dependencies
│   └── .env             # Environment variables
├── README.md            # Main documentation
├── RECOMMENDATIONS.md   # Feature recommendations
├── GITHUB_SETUP.md     # This file
└── .gitignore          # Git ignore rules
```

---

## 🏷️ Recommended Repository Tags

Add these topics to your repository (GitHub repo page → About → Settings):
- `language-learning`
- `thai-language`
- `english-learning`
- `react-native`
- `expo`
- `mobile-app`
- `fastapi`
- `mongodb`
- `education`
- `flashcards`
- `text-to-speech`
- `speech-recognition`
- `typescript`
- `python`

---

## 📝 .gitignore Important Entries

Your `.gitignore` should include (already configured):
```
# Sensitive
.env
*.env
.env.local

# Dependencies
node_modules/
__pycache__/

# Build
dist/
build/
.expo/

# IDE
.vscode/
.idea/
```

---

## 🔄 Ongoing Development Workflow

### Daily Workflow
```bash
# Pull latest changes
git pull origin main

# Make changes...

# Stage changes
git add .

# Commit
git commit -m "feat: Add new feature description"

# Push
git push origin main
```

### Branch Strategy
```bash
# Create feature branch
git checkout -b feature/new-lesson-type

# Work on feature...
git add .
git commit -m "feat: Add image-based lessons"

# Push branch
git push origin feature/new-lesson-type

# Create Pull Request on GitHub
# After approval, merge to main
```

---

## 📦 GitHub Releases

### Creating a Release
```bash
# Tag version
git tag -a v1.0.0 -m "LangSwap v1.0.0 - Initial Release"
git push origin v1.0.0
```

Then on GitHub:
1. Go to Releases → Draft a new release
2. Choose tag: v1.0.0
3. Release title: "LangSwap v1.0.0 - Bidirectional Learning Platform"
4. Description:
```
## 🎉 Initial Release

### Features
- 350+ comprehensive lessons
- Bidirectional learning (Thai ⇄ English)
- Speech-to-Translate
- 30+ UI languages
- Dark mode with OLED optimization
- User authentication
- Progress tracking
- Image support for lessons

### Download
- iOS: Coming soon to App Store
- Android: Coming soon to Play Store

### Documentation
See README.md for full setup instructions.
```

---

## 🤝 Collaborator Setup

To add collaborators (like Northerner1993@gmail.com):
1. Repository → Settings → Collaborators
2. Add people → Enter email or username
3. They'll receive an invitation

---

## 🚨 Important Notes

### Before First Push
1. ✅ Review all files for sensitive data
2. ✅ Ensure `.env` files are in `.gitignore`
3. ✅ Remove any API keys from code
4. ✅ Update README with accurate information

### Security Best Practices
- ❌ Never commit `.env` files
- ❌ Never commit API keys or passwords
- ✅ Use environment variables
- ✅ Regular security audits
- ✅ Keep dependencies updated

---

## 📊 GitHub Actions (CI/CD) - Optional

Create `.github/workflows/ci.yml`:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          yarn install
      - name: Run tests
        run: |
          cd frontend
          yarn test
```

---

## 📱 App Store Deployment

### iOS App Store
1. Enroll in Apple Developer Program ($99/year)
2. Configure app identifiers
3. Build with EAS:
```bash
cd frontend
eas build --platform ios
```
4. Submit via App Store Connect

### Google Play Store
1. Create Developer Account ($25 one-time)
2. Build APK/AAB:
```bash
cd frontend
eas build --platform android
```
3. Upload to Google Play Console

---

## 📧 Contact & Support

**Developer:** Jake Adamson  
**Email:** jakemadamson2k14@gmail.com  
**Repository:** https://github.com/YOUR_USERNAME/langswap-app

---

## 🎓 Learning Resources

- [Expo Documentation](https://docs.expo.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Native](https://reactnative.dev/)
- [MongoDB](https://www.mongodb.com/docs/)

---

**Ready to push your code to GitHub!** 🚀

Follow steps 1-5 above to get started. If you encounter any issues, refer to the troubleshooting section in README.md.
