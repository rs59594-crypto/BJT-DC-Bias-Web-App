# Validation — ตรวจสอบความถูกต้องของผลลัพธ์ (Lab 02 · 2/2569)

## 1. ชุดข้อมูลอ้างอิง

VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ, RE = 1 kΩ, β = 100, VBE = 0.70 V

## 2. เปรียบเทียบค่า: คำนวณมือ vs โปรแกรม (หน้าเว็บ) vs unit tests

| ปริมาณ | คำนวณมือ (design §10) | หน้าเว็บ (4 ทศนิยม) | unit test (SI, delta) | ตรงกัน |
|---|---|---|---|---|
| VTH | 2.16393 V | 2.1639 | 2.163934 (δ1e-3) | ✅ |
| RTH | 18.0328 kΩ | 18.0328 | 18032.7869 Ω (δ1e-3) | ✅ |
| IB | 12.2986 µA | 12.2986 | 1.229858e-5 A (δ1e-7 ผ่าน IC) | ✅ |
| IC | 1.22986 mA | 1.2299 | 1.229858e-3 A (δ1e-7) | ✅ |
| IE | 1.24216 mA | 1.2422 | (β+1)·IB (δ1e-12) | ✅ |
| VE | 1.24216 V | 1.2422 | 1.242157 (δ1e-5) | ✅ |
| VB | 1.94216 V | 1.9422 | 1.942157 (δ1e-5) | ✅ |
| VC | 9.29431 V | 9.2943 | 9.294312 (δ1e-5) | ✅ |
| VCE | 8.05216 V | 8.0522 | 8.052155 (δ1e-5) | ✅ |
| Region | Forward-Active | Forward-Active | forward-active | ✅ |

ค่ามือตรวจสอบด้วยเลขคณิตเศษส่วนแท้: IB = 54473/4429210000 A (ดู design-note.md §10)

## 3. เคส validation / region ที่ทดสอบแล้ว (ผ่านทั้งหมด)

| เคส | อินพุต | ผลลัพธ์ที่คาด | ทดสอบโดย |
|---|---|---|---|
| Cutoff | R2 = 5 kΩ (VTH = 0.5714 < VBE) | region cutoff + warning | `test_cutoff_region`, `test_post_cutoff_warning` |
| Saturation | RC = 10 kΩ (VCE ติดลบตามสูตร) | region saturation + warning | `test_saturation_region`, `test_post_saturation_warning` |
| ขอบเขต VCE = 0.2 V | RC = 8584 Ω → VCE ≈ 0.2007 → active · RC = 8590 Ω → VCE ≈ 0.1934 → saturation | ใช้เปรียบเทียบ `<` เท่านั้น | `test_region_boundary_near_vce_02` |
| VBE ติดลบ | vbe = −0.7 | BiasError.field == "vbe" | `test_negative_vbe_raises` |
| R = 0 / ติดลบ | r1 = 0, rc = −100 | BiasError | `test_zero_resistor_raises` |
| β ≤ 0 | beta = 0, −5 | BiasError | `test_invalid_beta_raises` |
| VCC ≤ 0 | vcc = 0, −9 | BiasError | `test_invalid_vcc_raises` |
| β ใหญ่มาก | beta = 10000 | ทุกค่า finite | `test_large_beta_still_finite` |
| กรอกตัวหนังสือ | vcc = "abc" | HTTP 200 + error ไทย (ไม่ 500) | `test_post_non_numeric_error` |
| ฟิลด์ขาดหาย | ไม่ส่ง beta | HTTP 200 + error ไทย (ไม่ 500) | `test_post_missing_field_error` |

## 4. ผลการรัน test ใน venv (จำลองผู้ตรวจ — Acceptance A7)

```
.venv\Scripts\python.exe -m unittest discover -s tests -v
Ran 18 tests in 0.038s
OK
```

(บันทึกฉบับเต็มใน `docs/test-log.txt`)

## 5. ข้อจำกัดของแบบจำลอง

- **β คงที่** — จริง ๆ β แปรผันตามกระแส/อุณหภูมิ
- **VBE คงที่** — จริง ๆ VBE ≈ 0.6–0.7 V แปรผันตามกระแสและอุณหภูมิ (−2 mV/°C โดยประมาณ)
- **VCE_SAT = 0.2 V** เป็นค่าประมาณเพื่อการเตือน (จริง ๆ ≈ 0.1–0.3 V แล้วแต่ทรานซิสเตอร์)
- แบบจำลองเชิงเส้น (Linearized BJT) **ไม่ใช่** SPICE/ngspice — นอก Forward-Active โปรแกรมจะเตือนว่าค่าใช้อ้างอิงไม่ได้
- ไม่ครอบคลุม AC analysis / transient / อุณหภูมิ (อยู่นอกขอบเขตของ Lab 02)
