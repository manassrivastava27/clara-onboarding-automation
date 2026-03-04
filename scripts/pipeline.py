import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional

# Load your API key
load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# --- REQUIRED DATA SCHEMAS ---

class BusinessHours(BaseModel):
    days: Optional[str]
    start: Optional[str]
    end: Optional[str]
    timezone: Optional[str]

class CallTransferRules(BaseModel):
    timeouts: Optional[str]
    retries: Optional[str]
    failure_message: Optional[str]

class EmergencyRoutingRules(BaseModel):
    who_to_call: Optional[str]
    order: Optional[str]
    fallback: Optional[str]

class AccountMemo(BaseModel):
    account_id: str
    company_name: Optional[str]
    business_hours: BusinessHours
    office_address: Optional[str]
    services_supported: List[str]
    emergency_definition: List[str]
    emergency_routing_rules: EmergencyRoutingRules
    non_emergency_routing_rules: Optional[str]
    call_transfer_rules: CallTransferRules
    integration_constraints: Optional[str]
    after_hours_flow_summary: Optional[str]
    office_hours_flow_summary: Optional[str]
    questions_or_unknowns: List[str]
    notes: Optional[str]

class RetellAgentSpec(BaseModel):
    agent_name: str
    voice_style: str
    system_prompt: str
    key_variables: dict
    tool_invocation_placeholders: str
    call_transfer_protocol: str
    fallback_protocol: str
    version: str

# --- SYSTEM PROMPT ---
v1_system_instruction = """
You are an expert automation engineer extracting data from a demo call transcript to configure an AI voice agent.
Your task is to generate a structured Account Memo and a Retell Agent Draft Spec based ONLY on the provided transcript.

CRITICAL RULES:
1. NO HALLUCINATION: If a detail (like business hours, address, or transfer timeout) is missing, leave the field null/empty. Do not guess.
2. If data is missing, explicitly list what is missing in the 'questions_or_unknowns' array.
3. The 'version' in the Retell Agent Spec must be 'v1'.
4. The system_prompt must include a strict business hours flow and after hours flow. Do NOT mention function calls to the caller.
"""

# Initialize the model with the strict JSON constraint for the Account Memo
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=v1_system_instruction,
    generation_config={
        "response_mime_type": "application/json",
        "response_schema": AccountMemo,
    }
)

# Initialize a second model specifically for the Retell Agent Spec schema
agent_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=v1_system_instruction,
    generation_config={
        "response_mime_type": "application/json",
        "response_schema": RetellAgentSpec,
    }
)

def process_demo_call(account_id: str, transcript_text: str):
    print(f"Processing Demo Call for Account: {account_id}...")
    
    # 1. Create the output directory if it doesn't exist
    output_dir = f"outputs/accounts/{account_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. Generate the Account Memo (v1)
    print("  -> Generating v1 Account Memo...")
    memo_response = model.generate_content(transcript_text)
    memo_json = json.loads(memo_response.text)
    
    with open(f"{output_dir}/v1_memo.json", "w") as f:
        json.dump(memo_json, f, indent=4)
        
    # 3. Generate the Retell Agent Spec (v1)
    print("  -> Generating v1 Retell Agent Spec...")
    agent_response = agent_model.generate_content(transcript_text)
    agent_json = json.loads(agent_response.text)
    
    with open(f"{output_dir}/v1_agent.json", "w") as f:
        json.dump(agent_json, f, indent=4)
        
    print(f"Success! v1 files saved in {output_dir}/")

# --- PIPELINE B: ONBOARDING & V2 UPDATES ---

v2_system_instruction = """
You are an expert automation engineer. You are receiving an existing v1 Account Memo (JSON) and a new Onboarding Call Transcript.
Your task is to UPDATE the account configuration based on the new transcript.

CRITICAL RULES:
1. Only update fields if the onboarding transcript explicitly changes or confirms them.
2. Preserve all other existing data from v1.
3. Resolve conflicts logically (Onboarding data overrides Demo data).
4. The 'version' in the Retell Agent Spec must be 'v2'.
5. NO HALLUCINATION. Do not guess missing details.
"""

# Initialize v2 models
v2_memo_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=v2_system_instruction,
    generation_config={"response_mime_type": "application/json", "response_schema": AccountMemo}
)

v2_agent_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=v2_system_instruction,
    generation_config={"response_mime_type": "application/json", "response_schema": RetellAgentSpec}
)

# A simple model to write the markdown changelog
changelog_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction="You are a system tracking configuration changes. Compare the provided v1 JSON and v2 JSON. Write a short, clear Markdown changelog explaining exactly what changed and why."
)

def process_onboarding_call(account_id: str, onboarding_transcript: str):
    print(f"\nProcessing Onboarding Call for Account: {account_id}...")
    output_dir = f"outputs/accounts/{account_id}"
    
    # 1. Load the existing v1 memo
    try:
        with open(f"{output_dir}/v1_memo.json", "r") as f:
            v1_memo_str = f.read()
    except FileNotFoundError:
        print(f"Error: v1_memo.json not found for {account_id}. Run Pipeline A first.")
        return

    # 2. Combine v1 data with new transcript
    prompt = f"EXISTING V1 MEMO:\n{v1_memo_str}\n\nNEW ONBOARDING TRANSCRIPT:\n{onboarding_transcript}"

    # 3. Generate v2 Memo
    print("  -> Generating v2 Account Memo...")
    v2_memo_response = v2_memo_model.generate_content(prompt)
    v2_memo_json = json.loads(v2_memo_response.text)
    with open(f"{output_dir}/v2_memo.json", "w") as f:
        json.dump(v2_memo_json, f, indent=4)

    # 4. Generate v2 Agent Spec
    print("  -> Generating v2 Retell Agent Spec...")
    v2_agent_response = v2_agent_model.generate_content(prompt)
    v2_agent_json = json.loads(v2_agent_response.text)
    with open(f"{output_dir}/v2_agent.json", "w") as f:
        json.dump(v2_agent_json, f, indent=4)

    # 5. Generate Changelog
    print("  -> Generating Changelog...")
    changelog_prompt = f"V1 CONFIG:\n{v1_memo_str}\n\nV2 CONFIG:\n{json.dumps(v2_memo_json)}"
    changelog_response = changelog_model.generate_content(changelog_prompt)
    with open(f"{output_dir}/changelog.md", "w") as f:
        f.write(changelog_response.text)

    print(f"Success! v2 files and changelog saved in {output_dir}/")

# --- BATCH PROCESSING ENTIRE DATASET ---
import glob

def run_full_pipeline(data_folder: str = "data"):
    print("Starting Batch Processing...")
    
    # Find all demo transcripts in the data folder
    demo_files = glob.glob(f"{data_folder}/*_demo.txt")
    
    if not demo_files:
        print(f"No demo files found in {data_folder}/. Please add files like 'account1_demo.txt'")
        return

    for demo_path in demo_files:
        # Extract account ID (e.g., 'data\account1_demo.txt' -> 'account1')
        filename = os.path.basename(demo_path)
        account_id = filename.replace("_demo.txt", "")
        
        # 1. Read Demo Transcript and Run Pipeline A
        with open(demo_path, "r", encoding="utf-8") as f:
            demo_text = f.read()
        process_demo_call(account_id, demo_text)
        
        # 2. Check for Onboarding Transcript and Run Pipeline B
        onboarding_path = f"{data_folder}/{account_id}_onboarding.txt"
        if os.path.exists(onboarding_path):
            with open(onboarding_path, "r", encoding="utf-8") as f:
                onboarding_text = f.read()
            process_onboarding_call(account_id, onboarding_text)
        else:
            print(f"  -> No onboarding file found for {account_id}. Skipping Pipeline B.")

if __name__ == "__main__":
    run_full_pipeline()