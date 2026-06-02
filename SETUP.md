# 🚀 Mega A.R. GitHub App Setup Guide

Complete step-by-step guide to set up and deploy the Mega A.R. GitHub App.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Create GitHub App](#create-github-app)
3. [Clone and Configure](#clone-and-configure)
4. [Install Dependencies](#install-dependencies)
5. [Local Testing](#local-testing)
6. [Deploy to Production](#deploy-to-production)

---

## Prerequisites

- Python 3.8+
- Git
- GitHub account with access to create apps
- FFmpeg installed (`apt install ffmpeg` or `brew install ffmpeg`)
- CUDA-capable GPU (recommended) or CPU fallback
- Hugging Face account (for speaker diarization)

---

## Create GitHub App

### Step 1: Visit GitHub App Settings
1. Go to [https://github.com/settings/apps](https://github.com/settings/apps)
2. Click **"New GitHub App"** button

### Step 2: Fill in the Form

Use these values:

| Field | Value |
|-------|-------|
| **App Name** | `Mega A.R.` |
| **Description** | `Transcribing audio files in multiple formats into Arabic with the highest accuracy and multiple quality settings.` |
| **Homepage URL** | `https://github.com/mohamedsaid881288-ctrl/Mega-Marble` |
| **Webhook URL** | `https://your-domain.com/webhook` |
| **Webhook Secret** | Generate a secure secret (save this!) |

### Step 3: Set Permissions

**Repository Permissions:**
- ✅ Issues: `Read & write`
- ✅ Pull requests: `Read & write`
- ✅ Contents: `Read`

**Organization Permissions:**
- ✅ Members: `Read`

### Step 4: Subscribe to Events

- ✅ `Issues`
- ✅ `Pull request`
- ✅ `Issue comment`

### Step 5: Installation

- ✅ `Only on this account` (or select your organization)

### Step 6: Create App

Click **"Create GitHub App"**

---

## Clone and Configure

### Step 1: Clone Repository

```bash
git clone https://github.com/mohamedsaid881288-ctrl/Mega-Marble.git
cd Mega-Marble
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Get GitHub App Credentials

1. Go to your app settings (https://github.com/settings/apps)
2. Click on **"Mega A.R."**
3. Scroll down and generate a **Private Key**
4. Copy the private key (it will be in PEM format)
5. Note your **App ID**

### Step 4: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# GitHub App Configuration
GITHUB_APP_ID=12345          # Your app ID
GITHUB_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----
WEBHOOK_SECRET=your_webhook_secret_here

# Hugging Face Token (get from https://huggingface.co/settings/tokens)
HF_TOKEN=hf_your_token_here

# Transcription Settings
DEVICE=cuda                  # or 'cpu' if no GPU
BATCH_SIZE=4
COMPUTE_TYPE=float16
LANGUAGE_CODE=ar

# Server Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=False
```

---

## Install Dependencies

### Option 1: GPU with CUDA

```bash
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install -r requirements.txt
```

### Option 2: CPU Only

```bash
pip install --upgrade pip
pip install torch torchvision torchaudio
pip install -r requirements.txt
```

### Verify Installation

```bash
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

---

## Local Testing

### Step 1: Start the App

```bash
python app.py
```

You should see:
```
Mega A.R. GitHub App initialized
Starting Mega A.R. on 0.0.0.0:5000
```

### Step 2: Test Health Endpoint

In another terminal:
```bash
curl http://localhost:5000/health
```

You should get:
```json
{
  "status": "healthy",
  "app": "Mega A.R.",
  "timestamp": "2024-..."
}
```

### Step 3: Check Available Endpoints

```bash
# Get app status
curl http://localhost:5000/api/status

# Get supported formats
curl http://localhost:5000/api/formats

# Get quality levels
curl http://localhost:5000/api/quality-levels

# Get supported languages
curl http://localhost:5000/api/supported-languages
```

### Step 4: Test Webhook (Optional)

Use ngrok to expose local server:

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 5000
```

Update your GitHub App webhook URL to the ngrok URL:
1. Go to app settings
2. Update "Webhook URL" to your ngrok URL
3. Test by creating an issue/PR in your repo

---

## Deploy to Production

### Option 1: Heroku

```bash
# Install Heroku CLI
brew tap heroku/brew && brew install heroku  # macOS
# or download from https://devcenter.heroku.com/articles/heroku-cli

# Login to Heroku
heroku login

# Create app
heroku create mega-ar-app

# Set environment variables
heroku config:set GITHUB_APP_ID=your_id
heroku config:set GITHUB_PRIVATE_KEY="your_key"
heroku config:set WEBHOOK_SECRET=your_secret
heroku config:set HF_TOKEN=your_hf_token

# Deploy
git push heroku main
```

### Option 2: AWS/Azure/GCP

Create a Docker container:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Set environment
ENV FLASK_ENV=production

# Run app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]
```

Deploy using your platform's documentation.

### Option 3: Self-Hosted Server

```bash
# On your server (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y python3.10 python3-pip python3-venv ffmpeg

# Clone repository
git clone https://github.com/mohamedsaid881288-ctrl/Mega-Marble.git
cd Mega-Marble

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/mega-ar.service
```

Add this to the service file:

```ini
[Unit]
Description=Mega A.R. GitHub App
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/home/user/Mega-Marble
Environment="PATH=/home/user/Mega-Marble/venv/bin"
EnvironmentFile=/home/user/Mega-Marble/.env
ExecStart=/home/user/Mega-Marble/venv/bin/gunicorn --bind 0.0.0.0:5000 --timeout 120 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mega-ar
sudo systemctl start mega-ar
```

### Step 5: Update Webhook URL

1. Go to GitHub App settings
2. Update "Webhook URL" to your production domain
3. Keep the webhook secret

---

## Troubleshooting

### Port Already in Use
```bash
# Kill process using port 5000
lsof -ti:5000 | xargs kill -9
```

### CUDA/GPU Issues
```bash
# Force CPU mode
export DEVICE=cpu
python app.py
```

### Memory Issues
```bash
# Reduce batch size
export BATCH_SIZE=2
python app.py
```

### Missing Hugging Face Token
Get one from [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

---

## Testing the App

### Create Test Issue

1. Go to a GitHub repository you own
2. Create an issue with an audio file
3. Check if app posts a comment (may take a minute)

### Check Logs

```bash
# In production
heroku logs --tail  # Heroku
docker logs container_name  # Docker
journalctl -u mega-ar -f  # Systemd
```

---

## Security Checklist

- ✅ Never commit `.env` file
- ✅ Keep private key secure
- ✅ Use HTTPS for webhook URL
- ✅ Rotate webhook secret regularly
- ✅ Monitor app logs for errors
- ✅ Set up rate limiting if needed

---

## Support

For issues or questions:
1. Check the logs
2. Create an issue in the repository
3. Review the main README.md

---

**Congratulations! Mega A.R. is now set up and ready to transcribe Arabic audio! 🎉**