"""HTTP tests ของ Flask app (ใช้ test client ไม่ต้องรัน server จริง)

ทดสอบผ่านฟอร์มหน่วย kΩ ตามที่ผู้ใช้กรอกจริง และตรวจค่าที่แสดง
(4 ทศนิยม) ตรงกับค่าอ้างอิงที่ตรวจแล้วใน design-note.md §10
"""
import unittest

from app import app


def form(**overrides):
    """ฟอร์มอ้างอิงหน่วย kΩ (ค่า default ของหน้าเว็บ) พร้อม override ทีละฟิลด์"""
    fields = dict(vcc="12", r1="100", r2="22", rc="2.2", re="1",
                  beta="100", vbe="0.7")
    fields.update(overrides)
    return fields


ERROR_CLASS = b'class="card error"'   # error block ใน template (card + error)


class WebAppTest(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_get_index_200(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'name="vcc"', r.data)
        self.assertIn('คำนวณ'.encode(), r.data)

    def test_post_reference_results(self):
        r = self.client.post("/calculate", data=form())
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"8.0522", r.data)   # VCE [V]
        self.assertIn(b"1.2299", r.data)   # IC [mA]

    def test_post_cutoff_warning(self):
        r = self.client.post("/calculate", data=form(r2="5"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("Cutoff".encode(), r.data)

    def test_post_saturation_warning(self):
        r = self.client.post("/calculate", data=form(rc="10"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("Saturation".encode(), r.data)

    def test_post_negative_vcc_error(self):
        r = self.client.post("/calculate", data=form(vcc="-5"))
        self.assertEqual(r.status_code, 200)
        self.assertIn(ERROR_CLASS, r.data)

    def test_post_non_numeric_error(self):
        r = self.client.post("/calculate", data=form(vcc="abc"))
        self.assertEqual(r.status_code, 200)
        self.assertIn(ERROR_CLASS, r.data)

    def test_post_missing_field_error(self):
        data = form()
        del data["beta"]
        r = self.client.post("/calculate", data=data)
        self.assertEqual(r.status_code, 200)
        self.assertIn(ERROR_CLASS, r.data)


if __name__ == "__main__":
    unittest.main()
