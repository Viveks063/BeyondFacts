# 🚀 Beyond Facts AI Social Agent - Deployment Guide

This guide explains how to deploy the **Beyond Facts AI Social Agent** so it runs 24/7 in the cloud without needing your laptop to stay powered on.

---

## 🏗️ Architecture Overview

The system uses a **Queue + Scheduler + SQLite** architecture:
- `scheduler.py`: Checks current time & schedule slots (08:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00, 22:00).
- `generator.py`: Generates curiosity content targeting specific category queue.
- `poster.py`: Playwright high-DPI HTML render → PNG carousel → Cloudinary CDN upload.
- `publisher.py`: Posts multi-slide carousels to Instagram Graph API.
- `database.py`: Manages `posts` table in `history.db` to prevent duplicate posts and track performance.
- `analytics.py`: Evaluates engagement (saves, comments, likes) and dynamically updates schedule weights.

---

## 🌐 Option 1: GitHub Actions (Free, Recommended)

Runs `python scheduler.py --check` automatically on a scheduled 2-hour cron trigger.

### Setup Instructions:
1. Push this repository to GitHub.
2. Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**.
3. Add the following repository secrets:
   - `GEMINI_API_KEY`
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
   - `INSTAGRAM_ACCESS_TOKEN`
   - `INSTAGRAM_BUSINESS_ID`
4. The workflow in `.github/workflows/scheduled_post.yml` will automatically run every 2 hours and commit database state changes to maintain history!

---

## 🚂 Option 2: Railway (Daemon Process)

Runs `python scheduler.py --daemon` as a continuous 24/7 background worker.

### Setup Instructions:
1. Connect your GitHub repository to [Railway.app](https://railway.app).
2. Railway will detect the `Procfile` worker definition: `worker: python scheduler.py --daemon`.
3. In Railway **Variables**, add all keys from `.env`.
4. Deploy service. The daemon will check `check_schedule()` every minute and safely post on due slots.

---

## 🖥️ Option 3: VPS (Hetzner / Contabo / DigitalOcean)

Best for full control using Linux `crontab` or `systemd`.

### Setup via Crontab:
1. SSH into your VPS:
   ```bash
   ssh root@your-vps-ip
   ```
2. Clone repository & install dependencies:
   ```bash
   git clone <your-repo-url> social-agent
   cd social-agent
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install --with-deps chromium
   ```
3. Create `.env` file with your credentials.
4. Add crontab entry to run single check every hour at minute 0:
   ```bash
   crontab -e
   ```
   Add line:
   ```cron
   0 * * * * cd /root/social-agent && /root/social-agent/venv/bin/python scheduler.py --check >> /root/social-agent/scheduler.log 2>&1
   ```

---

## ☁️ Option 4: Render Cron

1. Create a **Cron Job** on [Render.com](https://render.com).
2. Connect your GitHub repository.
3. Render will pick up `render.yaml`.
4. Set schedule to: `0 */2 * * *`.
5. Add Environment Variables in Render Dashboard.

---

## 📊 Command Line Commands

- **Check schedule once**:
  ```bash
  python scheduler.py --check
  ```
- **Run daemon mode**:
  ```bash
  python scheduler.py --daemon
  ```
- **View today's posting schedule status**:
  ```bash
  python scheduler.py --status
  ```
- **Force test run a specific slot**:
  ```bash
  python scheduler.py --force 08:00
  ```
