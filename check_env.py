#!/usr/bin/env python3
"""Quick script to check if environment variables are set correctly"""

import os

print("🔍 Checking Environment Variables...\n")
print("="*60)

# Check Canvas Token
canvas_token = os.getenv("CANVAS_TOKEN")
if canvas_token:
    print(f"✅ CANVAS_TOKEN is set")
    print(f"   Length: {len(canvas_token)} characters")
    print(f"   Preview: {canvas_token[:10]}...{canvas_token[-5:]}")
else:
    print("❌ CANVAS_TOKEN is NOT set")
    print("   Run: export CANVAS_TOKEN='your-token-here'")

print()

# Check OpenAI Key
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    print(f"✅ OPENAI_API_KEY is set")
    print(f"   Length: {len(openai_key)} characters")
    print(f"   Preview: {openai_key[:10]}...{openai_key[-5:]}")
else:
    print("❌ OPENAI_API_KEY is NOT set")
    print("   Run: export OPENAI_API_KEY='your-key-here'")

print()
print("="*60)

if canvas_token and openai_key:
    print("✅ All environment variables are set! You can run the app.")
else:
    print("⚠️  Some environment variables are missing.")
    print("   Set them, then run this script again to verify.")

