# ArXiv to Local

Download and clean ArXiv TeX sources for LLM grounding. This project consists of a FastAPI backend (running in Docker) and a Firefox browser extension.

## 1. Prerequisites

- Docker and Docker Compose
- Firefox Browser

## 2. Installation

### Start the Server
Navigate to the root folder (where `docker-compose.yml` is) and run:

```bash
# Ensure the output directory exists or change the path in docker-compose.yml
# current default is /Users/ptemplie/Documents/ICLVault/Sources
docker compose up --build -d
```

### Load the Extension
1. Open Firefox and go to `about:debugging`.
2. Click **"This Firefox"** (left sidebar).
3. Click **"Load Temporary Add-on..."**.
4. Select the `extension/manifest.json` file.

## 3. Usage Instructions

### Run It
1. Go to an ArXiv paper (e.g., [https://arxiv.org/abs/1901.01753](https://arxiv.org/abs/1901.01753)).
2. Click the extension icon.
3. Type a descriptive name for the folder (e.g., `poet`).
4. Hit **Enter**.

### Result
Check your local output folder (as configured in `docker-compose.yml`). You will see a folder named after your input (e.g., `poet`) containing:

- **Raw .tex files**: All extracted source files from ArXiv.
- **_full_paper_context.txt**: A single file with all text combined and comments stripped, ready for immediate drag-and-drop into your LLM.

## Project Structure

```text
arxiv_source/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
└── extension/
    ├── manifest.json
    ├── popup.html
    ├── popup.js
    └── icon.png
```
