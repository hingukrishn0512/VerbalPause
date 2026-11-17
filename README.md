# 🎙️ VerbalPause — Adversarial Voice AI Negotiation Platform

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://verbalpause-static.vercel.app/)
[![API Backend](https://img.shields.io/badge/API-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://verbalpause.onrender.com)
[![Database](https://img.shields.io/badge/Database-Neon%20Postgres-00E599?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech/)
[![Inference](https://img.shields.io/badge/Inference-Groq%20Llama--3.3%2070B-FF6F00?style=for-the-badge&logo=fastapi&logoColor=white)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

> **VerbalPause** is an adversarial, real-time voice AI sales and negotiation simulator built to train candidates, sales reps, and founders against realistic buyer friction.

Unlike passive, overly polite chatbots that wait for scripted pitches, **VerbalPause** simulates real high-stakes calls: buyers barge in when you monologue, lose patience over buzzwords, challenge pricing on the spot, and remember your performance over time.

---

### 🌐 Live Production Deployments

* **Frontend (Edge UI):** [https://verbalpause-static.vercel.app/](https://verbalpause-static.vercel.app/)
* **Backend (FastAPI Voice Engine):** [https://verbalpause.onrender.com](https://verbalpause.onrender.com)
* **Cloud Database:** [Neon Serverless PostgreSQL](https://neon.tech/)

---

## 🥊 Where Conventional Tools Fall Short & How VerbalPause Wins

| Problem in Existing Tools (Hyperbound, Second Nature, Yoodli) | VerbalPause Architectural Breakthrough |
| :--- | :--- |
| **Enterprise Lock-in & \$20K Minimums**: Legacy tools take months to implement with clunky LMS overhead. | **Instant Self-Serve Persona Synthesis**: Paste any prospect website URL & job title. Tavily crawls the company's tech stack and pain points into an active buyer in seconds. |
| **Overly Polite Bots**: Conventional bots wait through long silences and cave easily when pushed. | **Adversarial Emotion State Machine**: Tracks buyer *Patience* (100 $\to$ 0) and *Skepticism* (0 $\to$ 100). If you monologue for >12s without asking questions, the buyer **actively interrupts you**. |
| **Shallow Post-Call Grading**: Counting filler words ("ums") and WPM is a vanity metric and doesn't measure deal leverage. | **Moment-by-Moment "Leverage Drop" Replay**: Pinpoints the exact timestamp where you lost deal leverage, with a **1-click sandbox to re-record just that objection**. |
| **Stateless Drills**: Practice calls vanish into thin air without continuity. | **Neon PostgreSQL Persistence**: User authentication (bcrypt + JWT), daily practice streaks, and historical drill analytics stored permanently on the cloud. |

---

## 🏗️ System Architecture

```
                          ┌────────────────────────────────────────────────────────┐
                          │               Candidate Browser                        │
                          │   (Web Speech API / WebRTC Streaming Audio & VAD)      │
                          └───────────────────────────┬────────────────────────────┘
                                                      │
                                                      │  Real-Time Voice Streaming
                                                      ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │                           VerbalPause Backend Engine (FastAPI)                              │
 │                                                                                             │
 │   ┌────────────────────────┐      ┌─────────────────────────┐     ┌─────────────────────┐   │
 │   │ Real-Time STT Stream   │      │ Adversarial Emotion     │     │ Ultra-Fast TTS      │   │
 │   │ (Web Speech / Deepgram)│─────►│ State Machine           │────►│ (Streaming Audio)   │   │
 │   └────────────────────────┘      │ - Patience (100 -> 0)   │     └──────────┬──────────┘   │
 │                                   │ - Skepticism (0 -> 100) │                │              │
 │                                   │ - Monologue Interrupter │                │              │
 │                                   └────────────┬────────────┘                │              │
 │                                                │                             │              │
 │                                                ▼                             │              │
 │                                   ┌─────────────────────────┐                │              │
 │                                   │ Groq Llama-3.3 70B      │                │              │
 │                                   │ (300+ tok/s Inference)  │────────────────┘              │
 │                                   └────────────┬────────────┘                               │
 └────────────────────────────────────────────────┼────────────────────────────────────────────┘
                                                  │
                 ┌────────────────────────────────┴───────────────────────────────┐
                 ▼                                                                ▼
┌─────────────────────────────────┐                             ┌─────────────────────────────────┐
│     Post-Call Scoring Engine    │                             │    Neon Serverless Postgres     │
│ • Deal Leverage Curve (-10..+10)│                             │ • User Accounts & Bcrypt Hashes │
│ • Peak Gain vs Fatal Drop       │                             │ • JWT Session Authentication    │
│ • 1-Click Rewind Sandbox        │                             │ • Daily Practice Streaks        │
└─────────────────────────────────┘                             └─────────────────────────────────┘
```

---

## ⚡ Core Capabilities

### 1. Dynamic Emotion & Interruption State Machine
- **Patience Decay**: Decreases continuously if you monologue for >12 seconds without engaging the buyer with discovery questions.
- **Fluff Penalty**: Heavily penalizes marketing buzzwords (*"seamless"*, *"all-in-one"*, *"game-changer"*, *"synergy"*).
- **Active Barge-In**: If buyer patience drops below 35% or monologue exceeds 15s, the buyer actively interrupts:
  > *"Sorry to cut in, but I've got a hard stop in 3 minutes. What is the actual bottom-line ROI here?"*

### 2. 30-Second Instant Persona Generation
Paste any company URL (e.g., `https://stripe.com`) and target prospect role (e.g., *VP of Engineering*). The generator uses Tavily web intelligence to extract the target company's current challenges, engineering blogs, and market position, synthesizing a realistic adversarial persona.

### 3. "Rewind & Re-Pitch" Sandbox
Instead of a generic 75/100 scorecard, VerbalPause plots turn-by-turn deal leverage. You can jump directly to the fatal moment where you lost leverage, re-pitch your response, and test if your revised framing saves the deal.

### 4. Cloud Persistence & Daily Streaks
- **Neon Serverless PostgreSQL**: Stores candidate accounts, drill scorecards, and historical talk-to-listen ratios with zero cold-start delay.
- **JWT & Bcrypt Security**: Authenticated sessions with automatic practice streak tracking.

---

## 🛠️ Quickstart Guide

### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/hingukrishn0512/VerbalPause.git
cd VerbalPause

python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate # macOS/Linux

pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the project root:
```env
# LLM & Search Intelligence
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Neon Serverless PostgreSQL Database Connection
DATABASE_URL=postgresql://user:password@ep-xxxxxx-pooler.us-west-2.aws.neon.tech/neondb?sslmode=require
```

### 3. Launch the Server

#### Option A: Native Python
```bash
uvicorn backend.app.main:app --reload --port 8000
```

#### Option B: Docker Compose
```bash
docker compose up --build
```

Open your browser to:
👉 **`http://localhost:8000`** to start roleplaying immediately!

---

## 🚀 Cloud Deployment

- **Backend (Render):** Deployed as a Python 3 Web Service connecting to Neon Serverless PostgreSQL via connection pooling.
- **Frontend (Vercel):** Deployed as an edge static application with automatic production backend routing.

See the complete step-by-step instructions in [DEPLOYMENT.md](DEPLOYMENT.md).

---

## 📄 License
Distributed under the MIT License.
