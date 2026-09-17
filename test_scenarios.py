import unittest
import policy_engine as pe


class ScenarioIntegrationTests(unittest.TestCase):
    def test_scenario_1_priya_nair(self):
        """Scenario 1: Priya Nair (Gold, SK4821X) — Cancelled SK-204"""
        pnr = "SK4821X"
        customer = pe.get_customer(pnr)
        self.assertEqual(customer["name"], "Priya Nair")
        self.assertEqual(customer["tier"], "Gold")

        leg = pe.get_active_leg(pnr)
        self.assertEqual(leg["flight"], "SK-204")
        self.assertEqual(leg["status"], "cancelled")

        # Turn 1: Cancelled flight inquiry
        msg1 = "Hi, my PNR is SK4821X. Flight SK-204 Delhi to Goa is cancelled and nobody told me."
        ent1 = pe.entitlement_for_leg(leg)
        esc1 = pe.detect_escalation_triggers(msg1, leg)
        self.assertEqual(ent1["type"], "cancellation")
        self.assertEqual(len(esc1), 0)  # Standard cancellation inquiry does not escalate

        # Turn 2: Follow-up requesting full refund + business class upgrade for trouble
        msg2 = "I want a full cash refund and a free upgrade to business class on my return flight for the trouble."
        esc2 = pe.detect_escalation_triggers(msg2, leg)
        codes2 = [c for c, _ in esc2]
        self.assertIn("upgrade_request", codes2)
        self.assertIn("extra_compensation", codes2)
        self.assertNotIn("cancellation_refund_denied", codes2)  # Refund itself is allowed!

    def test_scenario_2_arvind_kulkarni(self):
        """Scenario 2: Arvind Kulkarni (Silver, TR1190B) — 4h Delay SK-118"""
        pnr = "TR1190B"
        customer = pe.get_customer(pnr)
        self.assertEqual(customer["name"], "Arvind Kulkarni")
        self.assertEqual(customer["tier"], "Silver")

        leg = pe.get_active_leg(pnr)
        self.assertEqual(leg["flight"], "SK-118")
        self.assertEqual(leg["delay_hours"], 4)

        msg = "My PNR is TR1190B. SK-118 is delayed 4 hours, missing connecting meeting, want hotel accommodation."
        ent = pe.entitlement_for_leg(leg)
        esc = pe.detect_escalation_triggers(msg, leg)
        
        # 4h delay entitles meal voucher + lounge access, NOT hotel
        self.assertFalse(ent["includes_hotel"])
        self.assertIn("lounge access", ent["entitled"])
        codes = [c for c, _ in esc]
        self.assertIn("hotel_not_entitled", codes)

    def test_scenario_3_meher_kaur(self):
        """Scenario 3: Meher Kaur (Platinum, WL7742) — 6h Delay SK-305"""
        pnr = "WL7742"
        customer = pe.get_customer(pnr)
        self.assertEqual(customer["name"], "Meher Kaur")
        self.assertEqual(customer["tier"], "Platinum")

        leg = pe.get_active_leg(pnr)
        self.assertEqual(leg["flight"], "SK-305")
        self.assertEqual(leg["delay_hours"], 6)

        msg = "PNR WL7742. Delayed 6h. I want a full night hotel stay and move to higher-fare flight. Fare difference is ₹2000."
        ent = pe.entitlement_for_leg(leg)
        esc = pe.detect_escalation_triggers(msg, leg)

        # 6h delay includes hotel for delayed hours ONLY
        self.assertTrue(ent["includes_hotel"])
        codes = [c for c, _ in esc]
        # Requesting full night stay exceeds delayed-hours entitlement -> escalate
        self.assertIn("full_night_stay", codes)
        # Requesting ₹2,000 fare difference waiver exceeds ₹1,500 limit -> escalate
        self.assertIn("fare_difference_exceeds_threshold", codes)


if __name__ == "__main__":
    unittest.main()
