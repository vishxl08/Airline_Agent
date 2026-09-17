# Airline Disruption — Customer-Facing Resolution Agent

Assignment 3 submission. Built with **FastAPI**, **Deterministic Python Policy Engine**, **Groq API**, and a modern **HTML5/CSS3 Dashboard**.

---

## 🏛️ System Architecture

Policy math is **never** left to the language model. Python computes exact customer entitlements and escalation triggers deterministically from the assignment data pack. Groq is used solely for natural language response generation and empathetic tone formatting.

```
+---------------------+     HTTP POST     +----------------------------------+
| Customer / Tester   | ----------------> | FastAPI Server (app.py)          |
| Web UI (index.html) |                   +----------------------------------+
+---------------------+                                    |
                                                           | 1. Intent & PNR Extract
                                                           v
                                          +----------------------------------+
                                          | Policy Engine (policy_engine.py) |
                                          | • Computes Leg Entitlements      |
                                          | • Detects Prohibited Actions     |
                                          +----------------------------------+
                                                           |
                                                           | 2. Grounded Facts Injected
                                                           v
                                          +----------------------------------+
                                          | Groq LLM (Tone & Reply Only)     |
                                          +----------------------------------+
                                                           |
                                                           | 3. Action Audit Logged
                                                           v
                                          +----------------------------------+
                                          | SQLite DB (conversations.db)     |
                                          +----------------------------------+
```

---

## ⚡ Quick Start & Local Run

### 1. Environment Setup
```bash
python -m venv myenv
# Windows:
.\myenv\Scripts\activate
# macOS/Linux:
source myenv/bin/activate

pip install -r requirements.txt
```

### 2. Configure API Key
Copy `.env.example` to `.env` and add your free Groq API key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```

### 3. Run Application Server
```bash
uvicorn app:app --reload --port 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🧪 Automated Testing

Run the unit test suite and scenario integration test suite:
```bash
python test_policy_engine.py
python test_scenarios.py
```

---

## 📋 Assignment Scenario Test Matrix

| Scenario | Customer & PNR | Input Prompt | Expected Outcome |
|---|---|---|---|
| **Scenario 1** | Priya Nair (`SK4821X`) | SK-204 cancelled, nobody told her | Free rebook within 24h **or** full refund. Gold = priority seats only. |
| **Scenario 1 Follow-up** | Priya Nair (`SK4821X`) | Wants full cash refund **plus** free upgrade to business class on return flight | **Initiate refund**. **Refuse & escalate** business upgrade (prohibited action). |
| **Scenario 2** | Arvind Kulkarni (`TR1190B`) | SK-118 delayed 4h; wants hotel for missing meeting | Issue meal voucher + lounge. **Refuse hotel** (hotel requires >5h delay). Escalate exception. |
| **Scenario 3** | Meher Kaur (`WL7742`) | SK-305 delayed 6h; wants full night hotel + rebook on higher fare flight (₹2,000 diff) | Issue meal + lounge + hotel **for delayed hours only**. **Refuse full night**. **Escalate ₹2,000 fare waiver** (> ₹1,500 cap). |

---

## 📁 Repository Structure

```
├── data_pack.py          # Grounding customer profiles, booking data, service rules
├── policy_engine.py      # Deterministic entitlements & prohibited action detection engine
├── app.py                # FastAPI backend endpoints (/chat, /health, /history, /reset)
├── static/
│   └── index.html        # Interactive UI dashboard with live customer cards & status tags
├── test_policy_engine.py # Unit tests for policy rules & regexes
├── test_scenarios.py     # End-to-end integration tests for Scenarios 1, 2, and 3
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # Project documentation
```

---

## 📄 Presentation Deck (10-Slide PPT Content)
A complete slide-by-slide content outline for the presentation submission is provided in [presentation_slides.md](presentation_slides.md) (or generated in the assignment artifacts).

---

## 📦 Mandatory Submission Checklist
- [x] **Clean GitHub Repository**: Code pushed without `.env` or `conversations.db` (gitignored).
- [x] **Architecture Diagram**: Documented above and in presentation deck.
- [x] **Demo Video**: Uploaded to Google Drive with public/open access settings.
- [x] **10-Slide PPT Presentation**: Slide deck content prepared and ready.
