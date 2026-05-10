# Fact-Checker Frontend

A modern, ChatGPT-like web interface for uploading documents and verifying claims with AI-powered fact-checking.

## Features

- 📄 **Document Upload** - Drag-and-drop support for text files
- 🤖 **Multi-Model Support** - Switch between Gemini and Ollama models
- 💬 **Chat Interface** - Conversational fact-checking experience
- ✅ **Claim Extraction** - Automatically extract claims from documents
- 🔍 **Claim Verification** - Verify individual claims with evidence
- 📊 **Confidence Scores** - See confidence levels and supporting/contradicting evidence

## Quick Start

### Prerequisites
- Node.js 18+ installed
- Backend running on `http://localhost:8000`

### Setup (2 minutes)

```bash
# Install dependencies
npm install
```

### Run Development Server

```bash
npm run dev
```

Open **http://localhost:3000** in your browser

## Usage

1. **Start the Backend First**
   ```bash
   cd ../fact-checker
   python main.py
   ```

2. **Start Frontend Dev Server**
   ```bash
   npm run dev
   ```

3. **Upload a Document**
   - Drag-and-drop a .txt file or click to browse
   - Claims will be extracted automatically

4. **Verify Claims**
   - Click "Verify" on extracted claims or type manually
   - View evidence and explanations

5. **Switch Models**
   - Use model selector at top to toggle between Gemini/Ollama

## Project Structure

```
src/
├── app/
│   ├── page.tsx          # Main page
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles
├── components/
│   ├── Chat.tsx          # Main container
│   ├── MessageBubble.tsx  # Message display
│   ├── DocumentUpload.tsx # File upload
│   ├── ModelSelector.tsx  # Model selection
│   ├── ClaimsDisplay.tsx  # Claims list
│   └── VerificationResult.tsx # Results
├── hooks/
│   └── useChat.ts        # State management
└── lib/
    ├── api.ts            # API client
    └── types.ts          # Types
```

## Configuration

Edit `.env.local` to change backend URL:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Build & Deploy

```bash
npm run build
npm start
```

Deploy to Vercel: Push to GitHub and connect to Vercel dashboard.

## Tech Stack

- Next.js 16+ (React framework)
- Tailwind CSS (styling)
- TypeScript (type safety)
- Axios (HTTP client)
