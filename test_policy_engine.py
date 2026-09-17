import unittest

from data_pack import BOOKINGS, CUSTOMERS
import policy_engine as pe


class PolicyEngineTests(unittest.TestCase):
    def test_finds_known_pnrs(self):
        self.assertEqual(pe.find_pnr_in_text("my pnr is sk4821x please"), "SK4821X")
        self.assertEqual(pe.find_pnr_in_text("PNR WL7742"), "WL7742")
        self.assertIsNone(pe.find_pnr_in_text("no booking here"))

    def test_get_customer_profile(self):
        priya = pe.get_customer("SK4821X")
        self.assertEqual(priya["name"], "Priya Nair")
        self.assertEqual(priya["tier"], "Gold")

        arvind = pe.get_customer("TR1190B")
        self.assertEqual(arvind["name"], "Arvind Kulkarni")
        self.assertEqual(arvind["tier"], "Silver")

        meher = pe.get_customer("WL7742")
        self.assertEqual(meher["name"], "Meher Kaur")
        self.assertEqual(meher["tier"], "Platinum")

    def test_cancellation_entitlement(self):
        leg = pe.get_active_leg("SK4821X")
        ent = pe.entitlement_for_leg(leg)
        self.assertEqual(ent["type"], "cancellation")
        self.assertFalse(ent["includes_hotel"])
        joined = " ".join(ent["entitled"]).lower()
        self.assertIn("refund", joined)
        self.assertIn("rebooking", joined)

    def test_four_hour_delay_no_hotel(self):
        leg = pe.get_active_leg("TR1190B")
        ent = pe.entitlement_for_leg(leg)
        self.assertEqual(ent["delay_hours"], 4)
        self.assertFalse(ent["includes_hotel"])
        self.assertIn("lounge access", ent["entitled"])

    def test_six_hour_delay_includes_hotel_hours_only(self):
        leg = pe.get_active_leg("WL7742")
        ent = pe.entitlement_for_leg(leg)
        self.assertEqual(ent["delay_hours"], 6)
        self.assertTrue(ent["includes_hotel"])

    def test_cash_refund_on_cancellation_is_not_extra_compensation(self):
        leg = pe.get_active_leg("SK4821X")
        reasons = pe.detect_escalation_triggers("I want a full cash refund", leg)
        codes = [c for c, _ in reasons]
        self.assertNotIn("extra_compensation", codes)

    def test_upgrade_and_trouble_do_escalate(self):
        leg = pe.get_active_leg("SK4821X")
        reasons = pe.detect_escalation_triggers(
            "I want a full cash refund and a free upgrade to business class for the trouble",
            leg,
        )
        codes = [c for c, _ in reasons]
        self.assertIn("upgrade_request", codes)
        self.assertIn("extra_compensation", codes)

    def test_hotel_ask_on_4h_delay_escalates(self):
        leg = pe.get_active_leg("TR1190B")
        reasons = pe.detect_escalation_triggers(
            "My flight is delayed and I want hotel accommodation", leg
        )
        codes = [c for c, _ in reasons]
        self.assertIn("hotel_not_entitled", codes)

    def test_full_night_and_fare_diff_escalate(self):
        leg = pe.get_active_leg("WL7742")
        reasons = pe.detect_escalation_triggers(
            "I want a full night hotel stay and a flight with a ₹2000 fare difference",
            leg,
        )
        codes = [c for c, _ in reasons]
        self.assertIn("full_night_stay", codes)
        self.assertIn("fare_difference_exceeds_threshold", codes)

    def test_fare_difference_regex_variations(self):
        leg = pe.get_active_leg("WL7742")
        # Phrase: "the fare difference is 2000"
        r1 = pe.detect_escalation_triggers("the fare difference is 2000", leg)
        self.assertTrue(any(c == "fare_difference_exceeds_threshold" for c, _ in r1))

        # Phrase: "difference of 1800 rupees"
        r2 = pe.detect_escalation_triggers("rebook on alternate with difference of 1800 rupees", leg)
        self.assertTrue(any(c == "fare_difference_exceeds_threshold" for c, _ in r2))

        # Under limit: "difference of 1200"
        r3 = pe.detect_escalation_triggers("fare difference is 1200", leg)
        self.assertFalse(any(c == "fare_difference_exceeds_threshold" for c, _ in r3))

    def test_overnight_stay_escalates(self):
        leg = pe.get_active_leg("WL7742")
        reasons = pe.detect_escalation_triggers("I need an overnight hotel stay", leg)
        codes = [c for c, _ in reasons]
        self.assertIn("full_night_stay", codes)

    def test_different_payment_method_escalates(self):
        leg = pe.get_active_leg("SK4821X")
        reasons = pe.detect_escalation_triggers("Refund to a different card please", leg)
        codes = [c for c, _ in reasons]
        self.assertIn("different_payment_method", codes)

    def test_legal_threat_escalates(self):
        leg = pe.get_active_leg("SK4821X")
        reasons = pe.detect_escalation_triggers("I will sue you and take legal action", leg)
        self.assertTrue(any(c == "legal_threat" for c, _ in reasons))

    def test_resolve_pnr_switches_when_new_pnr_appears(self):
        self.assertEqual(pe.resolve_pnr("SK4821X", "My PNR is TR1190B"), "TR1190B")
        self.assertEqual(pe.resolve_pnr("SK4821X", "I still want a refund"), "SK4821X")

    def test_arvind_entitlement_is_not_cancellation(self):
        ent = pe.entitlement_for_leg(pe.get_active_leg("TR1190B"))
        self.assertEqual(ent["type"], "delay")
        self.assertNotEqual(ent["type"], "cancellation")


if __name__ == "__main__":
    unittest.main()
