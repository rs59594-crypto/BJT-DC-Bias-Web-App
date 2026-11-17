"""Unit tests ของโมดูลวิศวกรรม dc_bias.py

ค่าอ้างอิงทุกตัวคำนวณด้วยมือจากชุดข้อมูลในเอกสาร Lab (VCC=12 V, R1=100 kΩ,
R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V) และตรวจสอบด้วยเศษส่วนแท้
IB = 54473/4429210000 A ตาม docs/design-note.md §10
"""
import math
import unittest

from dc_bias import BiasError, calculate_dc_bias

# ชุดข้อมูลอ้างอิง (หน่วย SI: V, Ω, A)
REF = dict(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0, re=1_000.0,
           beta=100.0, vbe=0.70)


class CalculateDcBiasTest(unittest.TestCase):

    def test_reference_case(self):
        r = calculate_dc_bias(**REF)
        self.assertAlmostEqual(r["ic"], 1.229858e-3, delta=1e-7)   # IC [A]
        self.assertAlmostEqual(r["vce"], 8.052155, delta=1e-5)     # VCE [V]
        self.assertAlmostEqual(r["vb"], 1.942157, delta=1e-5)
        self.assertAlmostEqual(r["ve"], 1.242157, delta=1e-5)
        self.assertAlmostEqual(r["vc"], 9.294312, delta=1e-5)
        self.assertEqual(r["region"], "forward-active")
        self.assertEqual(r["warnings"], [])

    def test_ie_relation(self):
        r = calculate_dc_bias(**REF)
        self.assertAlmostEqual(r["ie"], (REF["beta"] + 1) * r["ib"], delta=1e-12)
        self.assertAlmostEqual(r["ic"], REF["beta"] * r["ib"], delta=1e-12)

    def test_thevenin(self):
        r = calculate_dc_bias(**REF)
        self.assertAlmostEqual(r["vth"], 2.163934, delta=1e-3)
        self.assertAlmostEqual(r["rth"], 18032.7869, delta=1e-3)

    def test_cutoff_region(self):
        r = calculate_dc_bias(**{**REF, "r2": 5_000.0})   # VTH = 0.5714 V < 0.7 V
        self.assertEqual(r["region"], "cutoff")
        self.assertGreaterEqual(len(r["warnings"]), 1)

    def test_saturation_region(self):
        r = calculate_dc_bias(**{**REF, "rc": 10_000.0})  # VCE ติดลบตามสูตร
        self.assertEqual(r["region"], "saturation")
        self.assertGreaterEqual(len(r["warnings"]), 1)

    def test_region_boundary_near_vce_02(self):
        r_active = calculate_dc_bias(**{**REF, "rc": 8_584.0})   # VCE ≈ 0.2007 V
        self.assertEqual(r_active["region"], "forward-active")
        r_sat = calculate_dc_bias(**{**REF, "rc": 8_590.0})      # VCE ≈ 0.1934 V
        self.assertEqual(r_sat["region"], "saturation")

    def test_negative_vbe_raises(self):
        with self.assertRaises(BiasError) as cm:
            calculate_dc_bias(**{**REF, "vbe": -0.7})
        self.assertEqual(cm.exception.field, "vbe")

    def test_zero_resistor_raises(self):
        with self.assertRaises(BiasError):
            calculate_dc_bias(**{**REF, "r1": 0.0})
        with self.assertRaises(BiasError):
            calculate_dc_bias(**{**REF, "rc": -100.0})

    def test_invalid_beta_raises(self):
        for bad in (0.0, -5.0):
            with self.assertRaises(BiasError):
                calculate_dc_bias(**{**REF, "beta": bad})

    def test_invalid_vcc_raises(self):
        for bad in (0.0, -9.0):
            with self.assertRaises(BiasError):
                calculate_dc_bias(**{**REF, "vcc": bad})

    def test_large_beta_still_finite(self):
        r = calculate_dc_bias(**{**REF, "beta": 10_000.0})
        for key in ("ib", "ic", "ie", "vb", "ve", "vc", "vce"):
            self.assertTrue(math.isfinite(r[key]))


if __name__ == "__main__":
    unittest.main()
