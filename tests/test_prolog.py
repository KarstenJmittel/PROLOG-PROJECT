import unittest
from prolog_engine import prolog_engine, to_prolog_atom

class TestGridRescueProlog(unittest.TestCase):

    def test_atom_sanitization(self):
        self.assertEqual(to_prolog_atom("residential_zone_1"), "residential_zone_1")
        self.assertEqual(to_prolog_atom("North District, Sector 4!"), "north_district_sector_4")
        self.assertEqual(to_prolog_atom(""), "unknown")
        # Ensure starts with lowercase or valid atom prefix
        res = to_prolog_atom("4th Street")
        self.assertTrue(res[0].isalpha() and res[0].islower())

    def test_feeder_fault_diagnosis(self):
        reports = [
            {"source_type": "control_room", "evidence_category": "feeder_trip"},
            {"source_type": "citizen", "evidence_category": "power_outage"}
        ]
        result = prolog_engine.analyze_incident(101, reports, location="residential_zone_1")
        self.assertEqual(result["fault"], "FEEDER FAULT")
        self.assertIn("feeder_alpha", result["suspect_component"])
        self.assertIn("substation_central", result["upstream_path"])

    def test_fallen_line_diagnosis(self):
        reports = [
            {"source_type": "citizen", "evidence_category": "sparks_on_pole"},
            {"source_type": "engineer", "evidence_category": "broken_wire"}
        ]
        result = prolog_engine.analyze_incident(102, reports, location="residential_zone_1")
        self.assertEqual(result["fault"], "FALLEN LINE / POLE")
        self.assertIn("repair", result["action_plan"].lower())

    def test_critical_hospital_priority(self):
        reports = [
            {"source_type": "citizen", "evidence_category": "power_outage"}
        ]
        result = prolog_engine.analyze_incident(103, reports, location="hospital_hub")
        self.assertEqual(result["severity"], "CRITICAL")
        self.assertIn("hospital", result["action_plan"].lower())

    def test_unknown_location_resilience(self):
        reports = [
            {"source_type": "citizen", "evidence_category": "other_hazard"}
        ]
        result = prolog_engine.analyze_incident(104, reports, location="Custom Far Suburb")
        self.assertIn("UNKNOWN", result["fault"])
        self.assertIsNotNone(result["action_plan"])

    def test_dynamic_rerouting_hospital_backup(self):
        # Default route to hospital: substation_north -> feeder_gamma -> transformer_c1 -> hospital_hub
        reports = [{"source_type": "citizen", "evidence_category": "power_outage"}]
        result_normal = prolog_engine.analyze_incident(105, reports, location="hospital_hub")
        self.assertIn("transformer_c1", result_normal["upstream_path"])

        # When transformer_c1 is marked down, Prolog reroutes via transformer_a2
        result_rerouted = prolog_engine.analyze_incident(106, reports, location="hospital_hub", down_nodes=["transformer_c1"])
        self.assertIn("transformer_a2", result_rerouted["upstream_path"])
        self.assertNotIn("transformer_c1", result_rerouted["upstream_path"])

    def test_cross_tie_loop_rerouting(self):
        # When both transformer_c1 and feeder_alpha are down, route via cross-tie transformer_b1 -> feeder_beta
        reports = [{"source_type": "citizen", "evidence_category": "power_outage"}]
        result = prolog_engine.analyze_incident(
            107, reports, location="hospital_hub", down_nodes=["transformer_c1", "feeder_alpha"]
        )
        self.assertIn("transformer_b1", result["upstream_path"])
        self.assertIn("feeder_beta", result["upstream_path"])

if __name__ == "__main__":
    unittest.main()

