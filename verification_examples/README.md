# Verification Examples

This folder contains quick "red team" cases for the safety system.

## Quiz Red Team Tests

We provide two test scripts to verify the quiz verification system:

### 1. Fake LLM Test (Fast, No API Key Required)

**File**: `red_team_quiz_test.py`

Creates intentionally flawed quiz questions and runs them through verification with a **fake LLM** that returns hardcoded responses. This is useful for:
- Quick testing without API costs
- CI/CD pipelines
- Understanding the verification structure

**Run it:**
```bash
cd canvas-copilot
python3 verification_examples/red_team_quiz_test.py
```

No API key required! You should see multiple ⚠️ items with issues detected by the fake LLM.

### 2. Real LLM Test (Requires OpenAI API Key)

**File**: `red_team_quiz_test_real_llm.py`

Tests the same flawed questions but uses **actual OpenAI API calls** to verify correctness. This shows how the verification system performs with real LLM reasoning.

**Setup:**
```bash
# Set your OpenAI API key
export OPENAI_API_KEY='your-key-here'

# Run the test
cd canvas-copilot
python3 verification_examples/red_team_quiz_test_real_llm.py
```

This will:
1. ✓ Perform structural verification (no API calls)
2. 🤖 Call OpenAI API for each question to verify factual correctness
3. 📊 Generate a detailed verification report
4. 💾 Save report to `red_team_verification_report_real_llm.txt`

**Expected Behavior:**
The system should detect issues in questions with:
- Wrong capitals (e.g., "Paris is capital of South Korea")
- Math errors (e.g., "2+2=5")
- Historical inaccuracies
- Ambiguous or opinion-based questions

## What Gets Tested?

Both scripts test the verification system's ability to catch:

1. **Structural Issues** (no LLM needed):
   - Too few options
   - Duplicate answers
   - Invalid correct_index
   - Questions without question marks
   - Extremely short/long text

2. **Factual Issues** (LLM verification):
   - Wrong answers marked as correct
   - Factual inaccuracies
   - Ambiguous questions
   - Multiple valid answers
   - Opinion-based questions

## Cost Considerations

- **Fake LLM test**: Free, instant
- **Real LLM test**: ~$0.01-0.02 per test run (using gpt-4o-mini)
  - 6 questions × ~500 tokens each ≈ 3000 tokens total
  - Uses gpt-4o-mini for cost efficiency

## Recommended Workflow

1. **Development**: Use fake LLM test for rapid iteration
2. **Before Deployment**: Run real LLM test to verify actual behavior
3. **CI/CD**: Use fake LLM test (fast, no secrets needed)
4. **Periodic Validation**: Run real LLM test weekly to ensure quality
