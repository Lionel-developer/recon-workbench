# Recon Workbench

A Python/FastAPI and JavaScript project for inspecting Nmap XML files.

## Module 1
- Local API and browser interface
- File uploads with server-side size limits
- XML parsing with entity and external-reference restrictions
- Nmap root checks and host-record counts

## Run on Windows
1. Create an environment: `py -m venv .venv`
2. Install dependencies: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
3. Start the server: `.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload`
4. Open http://127.0.0.1:8000/static/index.html