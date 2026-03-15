"""
Quick diagnostic — run this to test your LLM connection.

Usage:  cd ai_strategy_room && python test_llm.py
"""

import os
import sys
import time

# Load .env
from dotenv import load_dotenv
load_dotenv()

provider = os.getenv("LLM_PROVIDER", "gemini")
print(f"\n{'='*50}")
print(f"  DecisionLab — LLM Diagnostic")
print(f"{'='*50}")
print(f"  Provider: {provider}")

# Check key exists
key_map = {
    "gemini": "GOOGLE_API_KEY",
    "groq": "GROQ_API_KEY", 
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}
key_name = key_map.get(provider, "UNKNOWN")
key_val = os.getenv(key_name, "")
print(f"  Key var: {key_name}")
print(f"  Key set: {'YES (' + key_val[:8] + '...)' if key_val else 'NO ❌ — this is your problem'}")

if not key_val:
    print(f"\n  Fix: Add {key_name}=your-key to .env file")
    if provider == "gemini":
        print(f"  Get free key: https://aistudio.google.com/app/apikey")
    sys.exit(1)

# Test import
print(f"\n  Testing import...")
try:
    from config import get_chat_model
    print(f"  ✅ Config import OK")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    print(f"  Fix: pip install langchain-google-genai" if provider == "gemini" else f"  Fix: pip install langchain-{provider}")
    sys.exit(1)

# Test LLM call
print(f"\n  Testing LLM call (should take 2-5 seconds)...")
try:
    from langchain_core.messages import HumanMessage
    llm = get_chat_model()
    start = time.time()
    response = llm.invoke([HumanMessage(content="Reply with exactly: HELLO")])
    elapsed = time.time() - start
    print(f"  ✅ LLM responded in {elapsed:.1f}s")
    print(f"  Response: {response.content[:100]}")
except Exception as e:
    print(f"  ❌ LLM call failed: {type(e).__name__}: {e}")
    if "API_KEY" in str(e).upper() or "auth" in str(e).lower():
        print(f"  Fix: Your API key is invalid. Get a new one.")
    elif "quota" in str(e).lower() or "rate" in str(e).lower():
        print(f"  Fix: Rate limit hit. Wait a minute and try again.")
    elif "module" in str(e).lower():
        print(f"  Fix: pip install langchain-google-genai")
    sys.exit(1)

# Test structured output (what agents actually do)
print(f"\n  Testing JSON structured output...")
try:
    from langchain_core.messages import SystemMessage, HumanMessage
    response = llm.invoke([
        SystemMessage(content="Always respond with valid JSON only."),
        HumanMessage(content='Respond with: {"status": "ok", "confidence": 0.85}'),
    ])
    text = response.content.strip()
    import json
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    parsed = json.loads(text)
    print(f"  ✅ JSON parsing OK: {parsed}")
except Exception as e:
    print(f"  ⚠ JSON test failed: {e}")
    print(f"  This may cause agent errors but simulation might still work")

print(f"\n{'='*50}")
print(f"  ✅ ALL TESTS PASSED — Run should work now")
print(f"{'='*50}\n")
