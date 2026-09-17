# System Architecture & Process Flow Specification

This document provides a comprehensive technical breakdown of the architecture, component interaction, process flow, and policy decision trees for the **Customer-Facing Resolution Agent (Airline Disruption)**.

---

## 1. Architecture Overview & Design Philosophy

The core architectural requirement for an airline disruption resolution system is **strict deterministic compliance**. Letting a language model compute delay compensation thresholds or approve policy waivers introduces unacceptable risk of hallucination (e.g., approving unauthorized cash bonuses or free business-class upgrades).

To solve this, the application implements a **Hybrid Decoupled Architecture**:

1. **Deterministic Logic Layer (Python)**: Handles 100% of policy math, entitlement calculations, currency regex parsing, and escalation detection.
2. **Generative Language Layer (Groq LLM)**: Handles 100% of customer empathy, tone standardization, and natural language explanation using grounded facts injected by the logic layer.

---

## 2. High-Level Flowchart Architecture

```mermaid
flowchart TD
    subgraph Frontend ["1. Presentation Layer (Browser)"]
        UI["Web UI Dashboard (static/index.html)<br/>• Customer Profile Card<br/>• Scenario Preset Launchers<br/>• Applied vs Escalated Action Badges"]
    end

    subgraph Backend ["2. API & Routing Layer (FastAPI)"]
        API["FastAPI App Router (app.py)<br/>• POST /chat<br/>• GET /history/{session_id}<br/>• GET /health<br/>• POST /reset"]
        DB[(SQLite Database: conversations.db<br/>Table: records)]
    end

    subgraph Logic ["3. Grounding & Policy Evaluation Layer"]
        PACK["Data Pack (data_pack.py)<br/>• Grounded Profiles (Priya, Arvind, Meher)<br/>• Flight Leg Schedules & Delay Statuses<br/>• Service Rules Text"]
        ENGINE["Policy Engine (policy_engine.py)<br/>• Active Leg Identification<br/>• Entitlement Calculator<br/>• Currency & Fare Difference Regex<br/>• Prohibited Action Detector"]
    end

    subgraph LLM ["4. LLM Generation Layer (Groq API)"]
        GROQ["Groq Inference Endpoint<br/>Models: qwen/qwen3.8-27b / llama-3.3-70b<br/>Function: Empathetic Reply Generation Only"]
    end

    %% Process Sequence
    UI -->|"1. User Message (Text / PNR)"| API
    API -->|"2. Retrieve Active PNR & Leg Data"| PACK
    PACK -->|"3. Evaluate Customer Booking & Rules"| ENGINE
    ENGINE -->|"4. Return Computed Entitlements & Escalation Triggers"| API
    API -->|"5. Build System Prompt with Grounded Facts"| GROQ
    GROQ -->|"6. Return Formatted Empathetic Response"| API
    API -->|"7. Persist Audit Record (Action, Escalated flag)"| DB
    API -->|"8. Return JSON (Reply, Action Badges, Customer Data)"| UI
```

---

## 3. End-to-End Sequence & Process Flow

```
==================================================================================================
                                    END-TO-END PROCESS FLOW
==================================================================================================

[ User / Browser ]    [ FastAPI Router ]   [ Policy Engine ]    [ Groq LLM API ]    [ SQLite Audit DB ]
        │                     │                    │                   │                     │
        │ 1. POST /chat       │                    │                   │                     │
        │────────────────────>│                    │                   │                     │
        │                     │ 2. Resolve PNR &   │                   │                     │
        │                     │    Active Leg      │                   │                     │
        │                     │───────────────────>│                   │                     │
        │                     │                    │ 3. Compute        │                     │
        │                     │                    │    Entitlements & │                     │
        │                     │                    │    Escalations    │                     │
        │                     │                    │                   │                     │
        │                     │ 4. Return Facts    │                   │                     │
        │                     │<───────────────────│                   │                     │
        │                     │                                        │                     │
        │                     │ 5. POST Chat Completion (System Prompt)│                     │
        │                     │───────────────────────────────────────>│                     │
        │                     │                                        │                     │
        │                     │ 6. Generated Empathetic Reply Text    │                     │
        │                     │<───────────────────────────────────────│                     │
        │                     │                                                              │
        │                     │ 7. Write Record (session_id, action_taken, escalated)        │
        │                     │─────────────────────────────────────────────────────────────>│
        │                     │                                                              │
        │ 8. JSON Response    │                                                              │
        │<────────────────────│                                                              │
```

---

## 4. Policy Decision Trees & Guardrail Rules

### 4.1 Cancellation Rebooking & Refund Decision Tree

```mermaid
graph TD
    A["Flight Status: CANCELLED"] --> B{"Customer Request"}
    B -->|"Wants Rebooking"| C["Offer Free Rebooking within 24 Hours<br/>(Gold/Platinum: Priority Seat Allocation)"]
    B -->|"Wants Refund"| D["Initiate Full Cash Refund<br/>(Processed in 7 Business Days to Original Payment Method)"]
    B -->|"Demands Upgrade / Cash Bonus"| E["Initiate Refund/Rebook<br/>+ ESCALATE Upgrade/Bonus Request to Specialist Team"]
```

### 4.2 Delay Compensation Decision Tree

```mermaid
graph TD
    A["Flight Status: DELAYED"] --> B{"Delay Duration"}
    B -->|"< 3 Hours"| C["Issue INR 500 Meal Voucher"]
    B -->|"3 to 5 Hours"| D["Issue Meal Voucher + Lounge Access"]
    B -->|"> 5 Hours"| E["Issue Meal Voucher + Lounge Access + Hotel<br/>(Covering ONLY Delayed Hours, NOT Full Night)"]
    
    C --> F{"Customer Demands Hotel?"}
    D --> F
    F -->|"Yes"| G["Refuse Hotel (Requires >5h delay)<br/>+ ESCALATE Policy Exception Request"]
    
    E --> H{"Customer Demands Full Night Stay?"}
    H -->|"Yes"| I["Grant Delayed-Hours Hotel<br/>+ ESCALATE Full Night Request"]
```

### 4.3 Fare Difference Waiver & Prohibited Actions Matrix

```mermaid
graph TD
    A["Voluntary Rebook / Out-of-Policy Request"] --> B{"Check Request Type"}
    B -->|"Fare Difference Waiver"| C{"Fare Diff Amount"}
    C -->|"<= INR 1,500"| D["Waive Fare Difference"]
    C -->|"> INR 1,500"| E["ESCALATE to Supervisor for Approval"]
    
    B -->|"Threat of Legal Action / Formal Complaint"| F["ESCALATE Immediately to Specialist Support Team"]
    B -->|"Refund to Non-Original Payment Method"| G["Refuse & ESCALATE (Prohibited Action)"]
```

---

## 5. Security, Auditability, and Anti-Hallucination Guardrails

1. **System Prompt Fact Pinning**: The system prompt injects `json.dumps(facts)` containing `computed_entitlement` and `escalation_reasons`. The LLM is explicitly forbidden from generating claims outside these facts.
2. **Audit Logging**: Every turn writes `session_id`, `ts`, `role`, `message`, `action_taken`, and `escalated` flag to SQLite database `conversations.db`.
3. **Session Reset Isolation**: Each scenario execution starts with a clean session to prevent cross-customer data leakage.
