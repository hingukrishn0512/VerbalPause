# 🎙️ VerbalPause — Adversarial Voice AI Negotiation Platform

[![Python Version](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Groq Llama-3.3 70B](https://img.shields.io/badge/Inference-Groq%20Llama--3.3%2070B-FF6F00?style=for-the-badge&logo=fastapi&logoColor=white)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

An adversarial, real-time voice AI sales and negotiation simulator designed to train candidates and account executives against realistic buyer friction.

Unlike passive, overly polite bots that wait patiently for you to finish scripted pitches, **VerbalPause** simulates real B2B high-stakes calls: buyers interrupt when you monologue, lose patience over generic buzzwords, and challenge ROI on the spot.

---

## 🥊 Where Existing Solutions Fall Short & How VerbalPause Wins

| Problem in Existing Tools (Hyperbound, Second Nature, Yoodli) | VerbalPause Architectural Breakthrough |
| :--- | :--- |
| **Enterprise Lock-in & \$20K Minimums**: Tools like Second Nature take 2 months to implement with enterprise LMS overhead. | **30-Second Self-Serve Persona Synthesis**: Paste any prospect company URL and title. We extract their tech stack and pain points into an active buyer in seconds. |
| **Overly Polite Bots**: Conventional bots wait for long silences and cave easily when pushed. | **Adversarial Emotion State Machine**: Tracks buyer *Patience* (100 $\to$ 0) and *Skepticism* (0 $\to$ 100). If you monologue for >15s without asking questions, the buyer **actively interrupts you**. |
| **Shallow Post-Call Grading**: Counting filler words ("ums") and WPM is a commodity and doesn't measure deal leverage. | **Moment-by-Moment "Leverage Drop" Replay**: Pinpoints the exact timestamp where you lost deal leverage, with a **1-click sandbox to re-record just that objection**. |

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
                                                  ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │                           Post-Call Leverage & Scoring Engine                               │
 │                                                                                             │
 │   • Deal Leverage Curve: Turn-by-turn plot of who holds the upper hand (-10 to +10)         │
 │   • Peak Gain vs Fatal Drop: Pinpoints the exact second where price/objection caved         │
 │   • 1-Click Rewind Sandbox: Re-try the failed turn and hear how the buyer responds           │
 └─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Core Capabilities

### 1. Dynamic Emotion & Interruption State Machine
- **Patience Decay**: Decreases if you monologue for >12 seconds without engaging the buyer with discovery questions.
- **Fluff Penalty**: Heavily penalizes marketing buzzwords (*"seamless"*, *"all-in-one"*, *"game-changer"*).
- **Active Barge-In**: If buyer patience drops below 35% or monologue exceeds 16s, the buyer actively interrupts:
  > *"Sorry to cut in, but I've got a hard stop in 3 minutes. What is the actual bottom-line ROI here?"*

### 2. 30-Second Instant Persona Generation
Paste any company URL (e.g. `https://stripe.com`) and target prospect role (e.g. *VP of Engineering*). The generator uses Tavily web intelligence to research the company's tech stack, recent news, and hiring challenges, synthesizing an adversarial persona with real objections.

### 3. "Rewind & Re-Pitch" Sandbox
Instead of a generic 75/100 scorecard, VerbalPause pinpoints the exact moment of failure. You can click on the fatal objection, re-pitch with better ROI framing, and see if your new response saves the deal.

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
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
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

## 🚀 Cloud Deployment (Render + Vercel)

VerbalPause is designed for cloud-native deployment in minutes:
- **Backend (Render):** Deploy as a Docker Web Service with zero-config auto-deploys via `render.yaml`.
- **Frontend (Vercel):** Deploy as a global static edge application via `vercel.json`.

See the complete step-by-step instructions in [DEPLOYMENT.md](file:///C:/Users/Yash/Desktop/VerbalPause/VerbalPause/DEPLOYMENT.md).

---

## 📄 License
Distributed under the MIT License.
