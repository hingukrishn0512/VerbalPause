# VerbalPause Production Deployment Guide

This guide covers deploying **VerbalPause** to production:
- **Backend:** [Render](https://render.com) (FastAPI + Docker container with sub-second Groq inference)
- **Frontend:** [Vercel](https://vercel.com) (Global CDN static edge deployment)
- **Local Container:** Docker Compose (`docker compose up --build`)

---

## Architecture Overview

```
                      ┌────────────────────────────────────────┐
                      │            Vercel Frontend             │
                      │  https://verbalpause.vercel.app        │
                      └──────────────────┬─────────────────────┘
                                         │
                    HTTPS Requests / Web Speech API (Browser STT/TTS)
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │             Render Backend             │
                      │  https://verbalpause-backend.onrender  │
                      │      (Docker / FastAPI / Port 10000)   │
                      └──────────┬──────────────────┬──────────┘
                                 │                  │
                                 ▼                  ▼
                       Groq Llama-3.3 70B    Tavily Search API
                     (Sub-600ms Inference)  (Company Web Intel)
```

---

## Part 1: Local Docker Verification

To build and run the full stack locally inside a production Docker container:

1. **Verify your `.env` file** exists with your keys:
   ```env
   GROQ_API_KEY=your_groq_key
   TAVILY_API_KEY=your_tavily_key
   ELEVENLABS_API_KEY=your_elevenlabs_key
   ```

2. **Build and launch with Docker Compose**:
   ```bash
   docker compose up --build
   ```

3. **Verify the container is healthy**:
   - Web App: `http://localhost:8000`
   - Healthcheck: `http://localhost:8000/health`
   - API Docs: `http://localhost:8000/docs`

4. **Stop the container**:
   ```bash
   docker compose down
   ```

---

## Part 2: Deploying Backend to Render

### Method A: 1-Click Render Blueprint (Recommended)

1. Log into your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** $\to$ **Blueprint**.
3. Connect your GitHub repository: `https://github.com/hingukrishn0512/VerbalPause`.
4. Render will detect the `render.yaml` configuration automatically.
5. In the **Environment Variables** prompt, fill in:
   - `GROQ_API_KEY`: Your Groq API key
   - `TAVILY_API_KEY`: Your Tavily API key
   - `ELEVENLABS_API_KEY`: Your ElevenLabs API key
6. Click **Apply**.
7. Render will build the Docker container and provide a live URL, e.g.:
   `https://verbalpause-backend.onrender.com`

### Method B: Manual Web Service Setup on Render

1. Click **New +** $\to$ **Web Service**.
2. Select your repository: `hingukrishn0512/VerbalPause`.
3. Configure the service:
   - **Name:** `verbalpause-backend`
   - **Region:** Ohio or Oregon
   - **Language / Runtime:** `Docker` (Dockerfile Path: `./Dockerfile`)
   - **Instance Type:** `Free`
4. Under **Environment Variables**, add:
   - `PORT`: `10000`
   - `GROQ_API_KEY`: `your_key`
   - `TAVILY_API_KEY`: `your_key`
   - `ELEVENLABS_API_KEY`: `your_key`
5. Click **Create Web Service**.
6. Note down your public service URL: `https://<your-service-name>.onrender.com`.
7. Test the health endpoint: `https://<your-service-name>.onrender.com/health`.

---

## Part 3: Deploying Frontend to Vercel

1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** $\to$ **Project**.
3. Import your GitHub repository: `https://github.com/hingukrishn0512/VerbalPause`.
4. Project Configuration:
   - **Framework Preset:** `Other` (Vercel automatically detects `index.html` and `vercel.json`).
   - **Root Directory:** `./`
   - **Build & Output Settings:** Leave default (No build command needed for pure high-speed HTML/JS).
5. Click **Deploy**.
6. In ~15 seconds, your application is live globally on your Vercel URL:
   `https://verbalpause.vercel.app` (or similar).

---

## Part 4: Connecting Vercel Frontend to Render Backend

Once both are deployed:

1. Open your live Vercel app in the browser: `https://<your-app>.vercel.app`.
2. Click the **⚙️ API URL** button in the top right header.
3. Paste your Render backend URL:
   `https://verbalpause-backend.onrender.com`
4. Click **OK**.
5. The frontend will now route all persona synthesis, voice emotion state machine turns, and leverage analysis to your live Render backend!

*(Note: The setting is persisted in `localStorage` on your client. You can also deploy full-stack directly on Render where frontend and backend are hosted on the same origin with 0 configuration.)*

---

## Production Health & Monitoring

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/health` | `GET` | Service status & API key verification |
| `/docs` | `GET` | Interactive Swagger UI API documentation |
| `/api/personas/presets` | `GET` | Pre-calibrated buyer personas |
| `/api/personas/generate` | `POST` | 30-second AI Persona Synthesizer via Tavily + Groq |
| `/api/sessions/start` | `POST` | Session initialization & initial emotion state |
| `/api/sessions/{id}/turn` | `POST` | Real-time speech turn, monologue interruption check |
| `/api/sessions/{id}/end` | `POST` | Post-call leverage replay & grounded coaching scorecard |
| `/api/sessions/{id}/retry-turn` | `POST` | 1-Click Rewind & Re-Pitch Sandbox |
