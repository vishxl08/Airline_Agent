# 15-Minute Video Demo Script & Oral Defense (Viva) Guide

This document contains two complete resources for project submission and defense:
1. **Part A**: A minute-by-minute transcript and narration script for recording the **15-Minute Project Demo Video**.
2. **Part B**: A comprehensive **Oral Defense / Viva Q&A Guide** with anticipated evaluator questions and expert answers.

---

# Part A: 15-Minute Demo Video Script

## Video Overview & Checklist
- **Target Duration**: 15 Minutes (900 seconds)
- **Screen Layout**: Browser window showing `http://localhost:8000` alongside Terminal / Code Editor.
- **Microphone**: Clear audio narration explaining each step.
- **Google Drive Sharing**: Set link permissions to **"Anyone with the link can view"**.

---

## Timestamped Narration Script

### Section 1: Introduction & System Philosophy (00:00 – 02:30)
- **Visual**: Show project repository, README.md, and system architecture diagram.
- **Speaker Narration**:
  > *"Hello everyone. Welcome to the demonstration of the Customer-Facing Resolution Agent for Airline Disruption — Assignment 3 submission.*
  >
  > *In airline customer support, disruption handling requires two critical capabilities: first, deep empathy for frustrated passengers; second, 100% strict policy compliance. Standard AI agents often fail because they hallucinate unapproved compensation, free business upgrades, or unauthorized hotel nights.*
  >
  > *To solve this, our project implements a Decoupled Hybrid Architecture. Policy math, delay thresholds, refund eligibility, and escalation triggers are evaluated deterministically in Python. The Groq Language Model is used solely for natural language response generation and tone formatting based on computed facts."*

---

### Section 2: Scenario 1 Demo — Priya Nair (Gold Tier, SK4821X) (02:30 – 05:30)
- **Visual**: Navigate to browser `http://localhost:8000`. Click **1. Priya Nair (Cancelled)** preset.
- **Speaker Narration**:
  > *"Let's test Scenario 1 with Priya Nair, a Gold tier customer holding PNR SK4821X. Her flight SK-204 from Delhi to Goa was cancelled due to operational reasons.*
  >
  > *In Turn 1, Priya asks about her cancelled flight. Notice how the left sidebar dynamically populates Priya's profile: Gold Tier, 6 flights in the last 12 months, and active status CANCELLED. The Policy Engine identifies that under Cancellation Rule 1, Priya is entitled to a free rebooking within 24 hours OR a full cash refund. The agent presents both options and highlights her Gold priority seating benefit.*
  >
  > *Now, in Turn 2, Priya expresses frustration and demands a full cash refund PLUS a free upgrade to business class on her return flight for the trouble.*
  >
  > *Watch what happens: The system initiates her full cash refund because it is permitted under policy. However, it explicitly refuses the business class upgrade and triggers an Escalation Badge: `OFFERED_REBOOK_OR_REFUND | ESCALATED: upgrade_request; extra_compensation`. The agent handles the interaction empathetically while strictly enforcing policy boundaries."*

---

### Section 3: Scenario 2 Demo — Arvind Kulkarni (Silver Tier, TR1190B) (05:30 – 08:30)
- **Visual**: Click **2. Arvind Kulkarni (4h Delay)** preset.
- **Speaker Narration**:
  > *"Now let's move to Scenario 2 featuring Arvind Kulkarni, a Silver tier customer with PNR TR1190B. His flight SK-118 from Mumbai to Bengaluru is delayed by 4 hours.*
  >
  > *Arvind reports that he is missing an important connecting meeting and demands hotel accommodation.*
  >
  > *Let's analyze the Policy Engine's output: Under Delay Compensation Rule 2, delays under 3 hours receive a ₹500 meal voucher; delays between 3 and 5 hours receive a meal voucher AND lounge access. Hotel accommodation requires a delay of MORE than 5 hours.*
  >
  > *Therefore, the agent grants Arvind a meal voucher and lounge access, but correctly refuses the hotel accommodation. Because Arvind requested an out-of-policy exception, the agent tags the turn as `APPLIED_DELAY_COMPENSATION:meal voucher,lounge access | ESCALATED: hotel_not_entitled` and escalates the hotel exception to a human supervisor."*

---

### Section 4: Scenario 3 Demo — Meher Kaur (Platinum Tier, WL7742) (08:30 – 11:30)
- **Visual**: Click **3. Meher Kaur (6h Delay)** preset.
- **Speaker Narration**:
  > *"Scenario 3 covers Meher Kaur, a Platinum tier customer with PNR WL7742. Flight SK-305 from Delhi to Hyderabad is delayed 6 hours.*
  >
  > *Meher requests a full night's hotel stay and asks to be moved onto a different, higher-fare flight with a fare difference of ₹2,000.*
  >
  > *This scenario tests two critical boundary rules:*
  > 1. *First, hotel accommodation for delays over 5 hours covers ONLY the delayed hours portion, NOT a full night's stay.*
  > 2. *Second, under the Fare Difference Rule, agents can only waive fare differences up to ₹1,500. A ₹2,000 difference exceeds supervisor authorization limits.*
  >
  > *As shown on screen, the agent provides hotel accommodation for the 6 delayed hours, refuses the full night stay, and flags the ₹2,000 fare difference for supervisor escalation. The UI displays the badge `ESCALATED: full_night_stay; fare_difference_exceeds_threshold`."*

---

### Section 5: Architecture & Codebase Review (11:30 – 13:30)
- **Visual**: Switch to code editor. Show `policy_engine.py`, `app.py`, and `data_pack.py`.
- **Speaker Narration**:
  > *"Let's briefly review the backend codebase:*
  > - `data_pack.py` *contains the grounded customer records, flight schedules, and exact policy rules.*
  > - `policy_engine.py` *uses robust regex patterns to parse currency figures like ₹2,000 or 1,800 rupees, and evaluates escalation triggers using word boundaries.*
  > - `app.py` *runs our FastAPI server, constructs prompt facts, calls Groq, and logs every single turn into SQLite database `conversations.db` for full compliance auditing."*

---

### Section 6: Automated Test Verification & Conclusion (13:30 – 15:00)
- **Visual**: Open terminal and run `python test_policy_engine.py` and `python test_scenarios.py`. Show 100% pass output.
- **Speaker Narration**:
  > *"Finally, let's run our automated test suite in the terminal:*
  > - `python test_policy_engine.py` *executes 15 unit tests covering regexes, threshold math, and entitlement outputs — 100% Passed.*
  > - `python test_scenarios.py` *executes end-to-end integration tests for all 3 assignment scenarios — 100% Passed.*
  >
  > *All code, test suites, architecture diagrams, and documentation are available on our GitHub repository. Thank you for watching!"*

---

# Part B: Oral Defense & Viva Q&A Guide

### Q1: Why did you separate policy calculation from the LLM instead of writing a detailed prompt?
**Answer**:
> LLMs are probabilistic language generators, not deterministic logic execution engines. Even with strong system prompts, LLMs can hallucinate policy exceptions, miscalculate threshold math, or yield under persuasive user pressure. By processing entitlements and prohibited action detection in Python (`policy_engine.py`), we guarantee 100% policy compliance, zero numerical hallucination, and deterministic auditability.

### Q2: How does your system handle PNR identification and context switching?
**Answer**:
> The `policy_engine.py` module uses regex pattern matching (`SK4821X|TR1190B|WL7742`) to extract PNRs from free text. When a customer mentions a new PNR, `app.py` automatically updates the session state and switches context to the new customer's grounded booking facts and flight leg history.

### Q3: What inputs, sources, and assumptions were used in this implementation?
**Answer**:
> - **Sources**: Assignment 3 Data Pack (Wednesday, 23 September 2026 date context, Customer Profiles, Booking Data, Service Rules).
> - **Inputs**: Customer PNR strings, flight leg IDs, free-text passenger messages.
> - **Assumptions**: Operational cancellations are airline-caused; Gold/Platinum tiers receive priority seat allocation during rebooking; delay hotel coverage applies strictly to delayed hours portion (not full night).

### Q4: Which AI tools were used during development and what were their roles?
**Answer**:
> - **Groq LLM API (Qwen 27B / Llama 3.3 70B)**: Used at runtime for natural language synthesis and empathetic response formatting.
> - **FastAPI & Python Policy Engine**: Used for deterministic rule execution and API orchestration.
> - **SQLite3**: Used for per-turn compliance audit logging.
> - **Antigravity AI Assistant**: Used during development for pair-programming, regex optimization, unit test generation, and architecture documentation.

### Q5: How does the system handle fare difference waivers exceeding the policy limit?
**Answer**:
> `policy_engine.py` parses currency expressions (e.g. `₹2,000`, `2000 rupees`, `fare difference is 2000`). If the detected fare difference exceeds the INR 1,500 agent waiver limit, the engine attaches the `fare_difference_exceeds_threshold` escalation code. The system prompt instructs the LLM to inform the customer that supervisor approval is required, while `app.py` logs the escalation in SQLite and displays an escalation badge on the UI.
