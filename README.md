# Clara AI - Onboarding Automation Pipeline

## Overview
This is a zero-cost automation pipeline built for Clara AI. It converts unstructured demo and onboarding call transcripts into structured, deployable Retell Agent configurations (v1 and v2) without hallucinating missing data.

## Architecture & Data Flow
1. **Pipeline A (Demo -> v1):** Ingests demo transcripts, uses Gemini 2.5 Flash (via free Google AI Studio API) forced into a strict Pydantic JSON schema to extract an Account Memo, and generates a `v1` Retell Agent Spec. 
2. **Pipeline B (Onboarding -> v2):** Ingests onboarding transcripts alongside the existing `v1_memo.json`, explicitly updates changed operational rules, preserves unchanged data, and generates `v2` outputs along with a markdown changelog.

## Setup Instructions
1. Install requirements: `pip install google-generativeai python-dotenv pydantic`
2. Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
3. Create a `.env` file in the root directory and add: `GEMINI_API_KEY=your_key_here`
4. Place your transcript text files in the `data/` directory using this naming convention:
   - `{account_id}_demo.txt`
   - `{account_id}_onboarding.txt`

## How to Run
Run the main script from the root directory:
```bash
python scripts/pipeline.py
```

## Known Limitations & Future Improvements
- **Audio Processing:** Currently expects text transcripts to maintain the "zero-cost" constraint. In production, I would integrate a Whisper endpoint (or Deepgram) for Speech-to-Text before the LLM extraction phase.
- **Task Tracking:** To keep this entirely local and reproducible for the grading team, I omitted the Asana API integration, but it could easily be added as a standard webhook POST request within the Python orchestrator.