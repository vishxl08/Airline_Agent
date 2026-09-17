"""
Data Pack — Assignment 3: Customer-Facing Resolution Agent (Airline Disruption)
All data below is taken directly from the provided data pack. Nothing invented.
"""

CUSTOMERS = {
    "SK4821X": {
        "name": "Priya Nair",
        "tier": "Gold",
        "email": "priya.nair@example.com",
        "phone": "+91-98xxxxxxx1",
        "flights_last_12mo": 6,
        "prior_complaints": [
            {"type": "delayed baggage", "resolution": "voucher"}
        ],
    },
    "TR1190B": {
        "name": "Arvind Kulkarni",
        "tier": "Silver",
        "email": "arvind.kulkarni@example.com",
        "phone": "+91-98xxxxxxx2",
        "flights_last_12mo": 3,
        "prior_complaints": [],
    },
    "WL7742": {
        "name": "Meher Kaur",
        "tier": "Platinum",
        "email": "meher.kaur@example.com",
        "phone": "+91-98xxxxxxx3",
        "flights_last_12mo": 10,
        "prior_complaints": [
            {"type": "overbooking", "resolution": "tier-status upgrade"}
        ],
    },
}

# Each PNR maps to a list of flight legs for that booking
BOOKINGS = {
    "SK4821X": [
        {
            "flight": "SK-204",
            "route": "Delhi → Goa",
            "date": "2026-09-23",
            "scheduled_departure": "18:40",
            "status": "cancelled",
            "reason": "operational reasons",
        },
        {
            "flight": "Return",
            "route": "Goa → Delhi",
            "date": "2026-09-25",
            "scheduled_departure": "16:20",
            "status": "unaffected",
        },
    ],
    "TR1190B": [
        {
            "flight": "SK-118",
            "route": "Mumbai → Bengaluru",
            "date": "2026-09-23",
            "scheduled_departure": "07:10",
            "status": "delayed",
            "delay_hours": 4,
            "new_departure": "11:10",
        }
    ],
    "WL7742": [
        {
            "flight": "SK-305",
            "route": "Delhi → Hyderabad",
            "date": "2026-09-23",
            "scheduled_departure": "14:00",
            "status": "delayed",
            "delay_hours": 6,
            "new_departure": "20:00",
        }
    ],
}

# Sample prior conversations from the assignment — TONE ONLY, not policy, not these customers.
SAMPLE_TONE = """
TONE EXAMPLES (other customers — copy the style, not the facts):
Sample A — cancelled, nobody told them:
  Agent: Completely understand the frustration. I can see flight SK-190 was cancelled due to operational reasons. I can rebook you on the next available flight at no extra cost, or process a full refund. Which would you prefer?
Sample B — delay ruined their day:
  Agent: I'm sorry for the disruption. Your flight was delayed 3 hours 40 minutes, which qualifies for a meal voucher and lounge access under our policy. I've applied both to your account now.
Sample C — furious, formal complaint / legal action:
  Agent: I hear you, and I'm sorry this has been such a frustrating experience. I want to make sure this gets the right attention — I'm escalating this to our specialist support team right now, and they'll reach out to you directly.
"""

RULES_TEXT = """
EXERCISE DATE: Wednesday, 23 September 2026.

SERVICE RULES:
1. Cancellation Rebooking Rule: If a flight is cancelled by the airline, the customer is entitled to a
   free rebooking on the next available flight within 24 hours, OR a full refund — customer's choice.
2. Delay Compensation Rule:
   - Delay under 3 hours: ₹500 meal voucher
   - Delay more than 3 hours: meal voucher + lounge access
   - Delay more than 5 hours: meal voucher + lounge access + hotel accommodation
     (covering ONLY the delayed hours, NOT a full night's stay)
3. Refund Processing Rule: Refunds for airline-caused cancellations are processed in full within
   7 business days, to the ORIGINAL payment method only.
4. Fare Difference Rule: If a customer voluntarily rebooks on a higher-fare flight (not airline-caused),
   they must pay the fare difference. Agents cannot waive fare differences above ₹1,500 without
   supervisor approval.
5. Loyalty Tier Rule: Gold and Platinum customers get priority rebooking (first access to next-available
   seats) but NO additional compensation beyond standard policy.

ALLOWED ACTIONS:
- Rebook customer on next available flight within 24h at no charge (airline-caused disruption)
- Issue meal vouchers and lounge access per the delay compensation rule
- Arrange hotel accommodation for the delayed-hours portion only, where it qualifies
- Initiate a refund request for airline-caused cancellations
- Provide the customer's own booking and flight status information

PROHIBITED ACTIONS — MUST ESCALATE TO A HUMAN AGENT:
- Approving any compensation beyond the stated policy amounts
- Waiving a fare difference above ₹1,500
- Making exceptions for non-airline-caused disruptions (e.g. customer missed the flight)
- Handling threats of legal action or formal complaints — escalate immediately
- Processing refunds to a different payment method than the original
"""
