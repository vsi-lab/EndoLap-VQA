# EndoLap-VQA


# Data Setup Guide: YouTube Video Downloading (by Timestamp)

This guide documents the full setup needed to download YouTube video clips between specified start/end timestamps, given a CSV of links and timestamps (e.g. columns like `video_link`, `begin_time_stamp_in_min`, `end_time_stamp_in_min`).

Downloading requires real setup, because YouTube has layered anti-bot protections (age-restriction gating, signature obfuscation, "proof of origin" tokens). Each numbered section below fixes one specific layer. **Do them in order** — skipping ahead will cause confusing errors. It assumes **zero prior experience** with these tools.

### 0. Expected input format

A CSV with (at minimum) these columns:
- `serial_no` — unique ID per row, used as the output filename
- `video_link` — full YouTube URL
- `begin_time_stamp_in_min` / `end_time_stamp_in_min` — clip start/end, in minutes (comma-decimal format like `1,30` for 1 min 30 sec is supported and converted automatically)

### 1.1 Create conda env and Install yt-dlp

```bash
conda create -n endolap_vqa python=3.10 -y
conda activate endolap_vqa
export PATH="$CONDA_PREFIX/bin:$PATH" ; hash -r; which python
```
```
pip install -U yt-dlp
```

Keep this updated — YouTube changes frequently, and yt-dlp ships frequent patches. Re-run this command any time you hit a new/unexplained error.

### 1.2 Install ffmpeg

Required for merging separate video/audio streams and cutting timestamped segments.
```bash
# Debian/Ubuntu
sudo apt install ffmpeg

# Or check if already available:
ffmpeg -version
```
If you're on a shared server without `sudo` access and ffmpeg isn't installed, contact your system admin or use a conda-installed version: `conda install -c conda-forge ffmpeg`.

### 1.3 Export cookies (for authentication)

Some videos (age-restricted or otherwise gated) require you to be logged in.

1. Log into YouTube in a browser with an account in good standing.
2. Install a **Netscape-format cookie exporter** browser extension (e.g. "Get cookies.txt LOCALLY").
3. While on youtube.com, export cookies to a file, e.g. `cookies.txt`.

> ⚠️ **Treat this file like a password.** It contains live session tokens. Never paste its contents into chat, commit it to version control, or share it with anyone. If it's ever exposed, immediately change your Google account password to invalidate the leaked session (Google Account → Security → Password), then re-export a fresh file.

Re-export this file any time you change your account password, since old exports become invalid.

### 1.4 Install Node.js via nvm (user-local, no admin rights needed)

Needed as a JavaScript runtime dependency for later steps. `nvm` installs Node entirely under your own home directory — **safe on shared/institutional servers**, since it doesn't touch the system Node or affect other users.

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Load nvm into your current terminal session:
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Install latest LTS Node:
nvm install --lts

# Verify:
node --version   # should print v18.x or higher
```

> **Note:** `export NVM_DIR=...` must be re-run in every new terminal window, unless you've restarted your terminal after installation (which auto-adds it to your shell config).

### 1.5 Install Deno (JS challenge solver runtime)

YouTube requires solving a signature-obfuscation challenge to unlock video formats. yt-dlp uses Deno to do this.

```bash
curl -fsSL https://deno.land/install.sh | sh

# Add to PATH (also user-local, no admin needed):
export PATH="$HOME/.deno/bin:$PATH"

# Verify:
deno --version
```

> Like `nvm`, re-run the `export PATH=...` line in new terminal sessions unless your shell config was updated automatically.

### 1.6 Set up the PO Token provider (bypasses age-restriction blocking)

As of 2025–2026, cookies alone are often insufficient for age-restricted videos — YouTube also requires a **PO Token** (proof-of-origin token). This section sets up a small local server that generates these tokens for yt-dlp automatically.

**Without Docker** (works on servers where you can't install Docker):

```bash
git clone https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git
cd bgutil-ytdlp-pot-provider/server
npm install
npx tsc
node build/main.js
```

The last command starts a local server (default: `http://127.0.0.1:4416`) and **must stay running** in its own terminal window for the entire duration of your download session. Open a **separate terminal** for running your actual download script.

You should see:
```
Started POT server (v2.0.0) on address [::1]:4416, 127.0.0.1:4416.
```

## Commands to run:

### Download the videos

Start with downloading the videos. Make sure you have the csv and cookies file in the working directory.
```
cd EndoLap-VQA
```
Check if everything is installed properly, if not, run -- `pip install -r requirements.txt`
Once the env is ready, go ahead with the following command:
```
python download_videos.py --csv <path/to/csv file containing video links> --output <target directory> --cookies <cookies.txt>  
```

If would like to use directly from chrome (or any other), one can use `--cookies-from-browser <chrome/firefox/etc>` along with the `--username <...>` and `--password <...>`. The preferable method would be using `cookies.txt`.

NOTE: The cookies keep getting expired after some time, so one need to replace once the session is expired. 

### Splitting them into 45-sec chunks
Once the videos are downloaded, run the following command:
```
python split_videos.py --input <path/to/folder containing downloaded videos> --output <path/to/folder to save video_clips>
```



## Troubleshooting Reference

| Symptom | Cause | Fix |
|---|---|---|
| `Sign in to confirm your age` | No valid cookies, or cookies alone aren't enough | Steps 1.3 + 1.6 |
| `n challenge solving failed` | Missing JS runtime / challenge script | Steps 1.5 + 1.7 (`--remote-components`) |
| `Only images are available for download` | Same as above — real video formats blocked | Steps 1.5 + 1.7 |
| `Error reaching GET http://127.0.0.1:4416` | PO Token server (1.6) isn't running | Start it in its own terminal before running downloads |
| `Precondition check failed` / `HTTP Error 400` | yt-dlp outdated | `pip install -U yt-dlp` |
| `SyntaxError: Unexpected token '?'` while building bgutil server | Node.js version too old (< v14) | Step 1.4 (use nvm to install a current LTS version) |
| Script exits instantly, "No such file or directory" | Hardcoded path to another machine's Python | Use `sys.executable` instead of a hardcoded path |

---

## Security Notes

- **Never share your cookies.txt contents** with anyone, including in chat logs, screenshots, or version control. It contains live session authentication tokens equivalent to your password.
- If cookies are ever exposed, immediately change the associated Google account's password (Google Account → Security → Password) to invalidate the old session, then re-export fresh cookies.
