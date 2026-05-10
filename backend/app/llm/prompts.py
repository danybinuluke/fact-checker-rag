"""
Centralized prompt templates for the Fact-Checking RAG system.
"""

EXTRACTION_PROMPT = """You are a fact-extraction expert.

From the given text, extract exactly 5-10 KEY FACTUAL CLAIMS.

For EACH claim:
1. State the claim clearly (under 20 words)
2. List key entities (people, places, dates, numbers)
3. Rate your confidence this is factual (0.0-1.0)

IMPORTANT: Return ONLY valid JSON with no markdown or extra text.

Format:
{{
  "claims": [
    {{
      "claim": "...",
      "entities": [...],
      "confidence": 0.95
    }}
  ]
}}

Text:
{text}

JSON:"""


VERIFICATION_PROMPT = """You are a Hybrid Fact-Checking Agent. Your mission is to verify a claim by comparing your internal knowledge against the provided User Documents.

User Claim: "{user_claim}"

=== SOURCE 1: USER DOCUMENTS (Corpus) ===
{similar_claims_text}

=== SOURCE 2: YOUR INTERNAL KNOWLEDGE ===
(Use your own training data)

=== INSTRUCTIONS ===
1. **Be Decisive**: If you know a claim is true or false from your training knowledge, give a status of SUPPORT or CONTRADICTION. Do NOT default to NEUTRAL just because the documents are silent.
2. **Identify Corroboration**:
   - If BOTH agree: Status is SUPPORT, Source is "both" (Corroborated).
   - If only YOU know it: Status is SUPPORT/CONTRADICTION, Source is "training" (Unverified by docs).
   - If only DOCS know it: Status is SUPPORT/CONTRADICTION, Source is "corpus" (External evidence).
   - If they DISAGREE: Status is CONTRADICTION, Source is "both" (Conflict detected).

=== OUTPUT (JSON) ===
Return EXACTLY this JSON structure:
{{
  "status": "SUPPORT|CONTRADICTION|NEUTRAL",
  "confidence": 0.0,
  "corpus_confidence": 0.0,
  "training_confidence": 0.0,
  "source": "both|corpus|training",
  "explanation": "Clearly state what you know vs what the documents say.",
  "supporting": ["Quotes from docs OR facts from your knowledge"],
  "contradicting": ["Conflicting quotes or facts"]
}}

JSON:"""
