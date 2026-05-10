# 🎯 Fact-Checking RAG System - Production-Ready

## 📝 PROJECT EXPLANATION

### The Simplest Explanation (1 Sentence)
**An AI system that reads documents, extracts claims, and then checks if those claims are corroborated, contradicted, or supported by other documents in the collection.**

---

## What The System Does (3 Steps)

### Step 1: Upload Documents
You give the system some documents (text or PDF):
- "Steve Jobs founded Apple in 1976"
- "Apple was founded in California"
- "Steve Jobs left Apple in 2011"

### Step 2: Extract Claims
The system automatically pulls out factual claims:
- Claim 1: "Steve Jobs founded Apple"
- Claim 2: "Apple in California"
- Claim 3: "Steve Jobs left in 2011"

### Step 3: Verify Claims
When you ask "Is Apple from 1976?" the system:
1. Looks through all stored claims
2. Finds similar ones
3. Checks if they support or contradict your claim
4. Returns a verdict with confidence score

---

## Real Example

**Your document:**
```
Apple Inc. was founded on April 1, 1976, by Steve Jobs and Steve Wozniak. 
The company is based in California.
```

**System extracts claims:**
```
Claim 1: "Apple founded April 1, 1976"
Claim 2: "Founded by Steve Jobs and Steve Wozniak"
Claim 3: "Based in California"
```

**You ask:** "Was Apple founded in 1975?"

**System responds:**
```
Status: CONTRADICTION
Confidence: 0.95 (95% sure)

Evidence against:
- "Apple founded on April 1, 1976" (95% confidence)

Explanation: Multiple sources confirm 1976, not 1975
```

---

## What Makes It Special: Dual LLM System

We use **two different AI models** for maximum reliability:

1. **Google Gemini (Primary - Production)**
   - Cloud-based, fast (1-3s), and highly accurate.
   - Handles all production claim extraction and verification.

2. **Ollama Qwen2 7B (Fallback - Local)**
   - Runs locally on your machine.
   - Automatically takes over if Gemini fails or if you are working offline.

---

## The Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI (Python) |
| **Primary AI** | Google Gemini 1.5 Flash |
| **Fallback AI** | Ollama Qwen2 7B |
| **Vector Search** | Sentence-Transformers (All-MiniLM-L6-v2) |
| **Parsing** | PyPDF, Python-Docx |
| **Frontend** | Next.js, React, TailwindCSS |

---

## 🚀 Quick Start

### 1. Get Gemini API Key
Go to [ai.google.dev](https://ai.google.dev/) and get a free API key.

### 2. Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to start fact-checking!
