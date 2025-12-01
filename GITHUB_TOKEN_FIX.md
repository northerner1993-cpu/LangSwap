# 🔐 GitHub Token Permission Fix

## ⚠️ Issue: Token Lacks Write Permissions

Your current token has **read-only** permissions. You need to create a new token with **write access** to push code.

---

## 🔧 Solution: Generate New Token with Proper Permissions

### Step 1: Go to GitHub Token Settings
Visit: https://github.com/settings/tokens?type=beta

### Step 2: Click "Generate new token" (Fine-grained)

### Step 3: Configure Token Settings

**Token Name**: `LangSwap Deployment Token`

**Expiration**: 
- 90 days (recommended) or Custom date

**Repository access**:
- ✅ **Only select repositories**
- Select: `LangSwap-`

**Repository permissions** (Click "Repository permissions" dropdown):

| Permission | Access Level | Why Needed |
|------------|--------------|------------|
| **Contents** | ✅ **Read and write** | Push code commits |
| **Metadata** | ✅ Read-only | Default (required) |
| **Pull requests** | Read and write | Optional (for PRs) |
| **Issues** | Read and write | Optional (for issue tracking) |
| **Actions** | Read and write | Optional (for CI/CD) |

### Step 4: Click "Generate token"

### Step 5: Copy the New Token
```
github_pat_[YOUR_NEW_TOKEN_HERE]
```

**⚠️ IMPORTANT**: Copy it immediately! You won't be able to see it again.

---

## 📝 Use the New Token

Once you have the new token, run these commands:

```bash
cd /app

# Remove old remote
git remote remove origin

# Add new remote with new token
git remote add origin https://[YOUR_NEW_TOKEN]@github.com/northerner1993-cpu/LangSwap-.git

# Push to GitHub
git push -u origin main
```

---

## 🔄 Alternative: Use GitHub CLI or SSH

### Option A: GitHub CLI (Recommended)
```bash
# Install GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Authenticate
gh auth login

# Push
cd /app
git push -u origin main
```

### Option B: SSH Key (More Secure)
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "jakemadamson2k14@gmail.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: https://github.com/settings/keys
# Then update remote to use SSH
git remote set-url origin git@github.com:northerner1993-cpu/LangSwap-.git
git push -u origin main
```

---

## 🆘 Quick Token Permission Checklist

When creating the token, make sure:
- ✅ Token type: **Fine-grained personal access token**
- ✅ Repository: **LangSwap-** selected
- ✅ Contents permission: **Read and write** ✅✅
- ✅ Metadata permission: **Read-only** (auto-selected)

---

## 🔗 Quick Links

- **Create Token**: https://github.com/settings/tokens?type=beta
- **SSH Keys**: https://github.com/settings/keys
- **Repository**: https://github.com/northerner1993-cpu/LangSwap-

---

## 📞 After Getting New Token

**Tell me the new token**, and I'll immediately push the code for you! Or follow the commands above to push manually.

---

**Error Encountered**: `403 Permission denied`  
**Root Cause**: Current token lacks write permissions to repository  
**Fix**: Generate new token with "Contents: Read and write" permission
