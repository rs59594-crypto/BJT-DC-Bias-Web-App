# Design Note — BJT DC Bias Web App (ENG29 2121 · Lab 02 · 2/2569)

- **วันที่:** 2026-11-10
- **Repo:** BJT-DC-Bias-Web-App (branch `main`)
- **สถานะ:** รอการอนุมัติจากนักศึกษา (Design Approval Gate)

## 1. Intent — เราสร้างอะไร และทำไม

สร้าง **Flask Web Application หลายไฟล์** สำหรับคำนวณ **DC Operating Point ของวงจร NPN Common-Emitter แบบ Voltage-Divider Bias** ภายในคาบ Lab 02 (180 นาที) เพื่อให้นักศึกษาได้เห็นความต่างระหว่างการเปิดไฟล์ HTML ตรง ๆ กับ Web App ที่มี **Python Backend คำนวณจริง** ผ่าน HTTP Request — Frontend/Backend/Template/Static/Tests แยกกันชัดเจน และทุกผลลัพธ์ตรวจสอบได้ด้วยการคำนวณอิสระ + Automated Tests + GitHub history

## 2. Goals

1. เปิดผ่าน `http://127.0.0.1:5000/` ได้ (ไม่ใช่ `file://`)
2. ฟอร์มรับ `VCC, R1, R2, RC, RE [kΩ]`, `β`, `VBE [V]` → POST ไปให้ Python คำนวณ
3. แสดง `VB, VE, VC, VCE [V]`, `IC [mA]` (+ `IB [µA]`, `IE [mA]`) **พร้อมหน่วยกำกับทุกค่า**
4. Validation: `R ≤ 0`, `β ≤ 0`, `VCC ≤ 0`, ค่าว่าง/ไม่ใช่ตัวเลข → ข้อความ error ภาษาไทยอ่านได้ หน้าเว็บไม่ล้ม
5. Warning เมื่อออกนอก Forward-Active: **Cutoff** (`VTH ≤ VBE`) และ **Saturation** (`VCE` ต่ำกว่าเกณฑ์ ≈ 0.2 V)
6. Tests: ≥3 unit tests (คณิตศาสตร์วิศวกรรม) + ≥1 Flask test client tests
7. README ทำตามแล้ว clone → รัน → ทดสอบได้ (Acceptance A7)

## 3. Non-goals (นอกขอบเขต Lab 02)

- AC Small-Signal, Gain, Bode Plot, Transient, Signal Generator, DC Load Line
- SPICE/ngspice solver, วงจร FET, Bias Types อื่น (Fixed/Emitter — สัปดาห์ถัดไป)
- Interactive schematic หรือ animation overlay
- รองรับผู้ใช้หลายคน / ฐานข้อมูล / deployment สาธารณะ

## 4. Anti-goals (ถ้าเกิดขึ้นถือว่าล้มเหลวแม้โปรแกรมรันได้)

- ค่าผลลัพธ์ hardcode ใน HTML/JS แทนการคำนวณใน Python
- แสดงค่าใน Cutoff/Saturation ว่าเป็นผลจำลองที่เชื่อถือได้โดยไม่มี Warning
- หน้าเว็บ crash (HTTP 500) เมื่อกรอกค่าผิด
- Commit `.venv/`, `__pycache__/`, `.env` หรือ credentials ขึ้น GitHub

## 5. Constraints

- สมการ (Forward-Active Approximation, β คงที่, VBE คงที่):
  `VTH = VCC·R2/(R1+R2)` · `RTH = R1R2/(R1+R2)` · `IB = (VTH−VBE)/(RTH+(β+1)RE)` ·
  `IC = βIB` · `IE = (β+1)IB` · `VE = IE·RE` · `VB = VE+VBE` · `VC = VCC−IC·RC` · `VCE = VC−VE`
- ชุดข้อมูลอ้างอิง: **VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, β=100, VBE=0.70 V**
- เครื่องมือ: Python 3.14.2, Flask 3.1.3, unittest (ตามคำสั่งในเอกสาร Lab: `python -m unittest discover -s tests -v`)
- เวลา: จบภายในคาบ — ทุกส่วนที่เพิ่มต้องตัดออกก่อนขยาย
- UI เป็นภาษาไทยเป็นหลัก (ตัวเลือกที่นักศึกษาเลือก) สัญลักษณ์วิศวกรรมเป็นอังกฤษ (VB, IC, kΩ)
- การ Commit ทำผ่าน GitHub Desktop ของนักศึกษา (ไม่ใช่ git CLI บนเครื่อง)

## 6. Approaches — ทางเลือกที่พิจารณา

| # | แนวทาง | ได้อะไร | เสียอะไร | ผล |
|---|---|---|---|---|
| 1 | HTML ไฟล์เดียว + JavaScript คำนวณใน Browser | ง่าย เร็ว ไม่ต้องรัน Server | **ขัดเป้าหมาย Lab** — ต้องการ Python Backend คำนวณจริงผ่าน HTTP; เปิด `file://` ไม่ผ่าน Acceptance | ❌ ตัดทิ้ง |
| 2 | **Flask multi-file + Jinja server-rendered** (POST form → Python → render ผล) | ตรงโจทย์ Lab ทุกข้อ, เรียนรู้ Frontend/Backend แยกชัด, จำนวนไฟล์น้อย ทำเสร็จในเวลา, test ง่ายด้วย Flask test client | หน้าเว็บ refresh ต่อการคำนวณ (ไม่มี SPA) — ยอมรับได้สำหรับ DC Bias | ✅ **เลือก** |
| 3 | Flask REST API (JSON) + JS fetch ฝั่ง Browser | สถาปัตยกรรม "สมัยใหม่" ขยายไป W3–W7 ได้ | ชิ้นงานเยอะขึ้น (JS + API + error handling สองชั้น) เกินเวลาคาบ โดยประโยชน์ที่ได้ไม่จำเป็นต่อ DC-only | ❌ เก็บไว้ภายหลัง |

**เหตุผลที่เลือก #2:** Lab กำหนดขอบเขตแคบมาก (DC Bias เท่านั้น) และเกณฑ์รับคือ "Server เรียก Python คำนวณและแสดงผลใน HTML" — แนวทาง server-rendered ตอบโจทย์นั้นตรงที่สุดด้วยจำนวนชิ้นส่วนน้อยที่สุด และโครงสร้างแยกไฟล์ (route/logic/template/static/tests) ยังยกระดับเป็น API ภายหลังได้โดยไม่ทิ้งงานเก่า

## 7. การตัดสินใจสำคัญ (Decisions)

1. **ภาษา UI:** ไทยเป็นหลัก + สัญลักษณ์วิศวกรรมอังกฤษ *(นักศึกษาเลือก)*
2. **หน่วยอินพุต:** ฟอร์มกรอก R เป็น **kΩ** (label กำกับชัด ตรงชุดข้อมูลตัวอย่าง 100, 22, 2.2, 1), VCC/VBE เป็น V, β ไม่มีหน่วย — ชั้น `app.py` แปลง kΩ→Ω ก่อนเรียกโมดูลวิศวกรรม
3. **หน่วยภายใน `dc_bias.py`:** SI ล้วน (V, Ω, **A**) — โมดูลไม่รู้จัก HTML/HTTP/หน่วยแสดงผล; ชั้นแสดงผลแปลง A→mA/µA เอง
4. **Route:** `GET /` แสดงฟอร์ม (มีค่า default ตามชุดอ้างอิง), `POST /calculate` คำนวณแล้ว render ผลกลับ (เปิดฟอร์ม+ผลในหน้าเดียว)
5. **Error handling:** input ผิด → render ฟอร์มเดิมพร้อมข้อความ error ไทย (HTTP 200, หน้าไม่ล้ม); `dc_bias.py` raise `BiasError` (subclass ของ `ValueError` พร้อมชื่อฟิลด์)
6. **Region logic:** `VTH ≤ VBE` → **Cutoff**; `VCE < 0.2 V` (VCE_SAT ประมาณ) → **Saturation** — ทั้งสองกรณีแสดงค่าที่คำนวณได้พร้อม Warning ว่าแบบจำลอง Forward-Active ใช้ไม่ได้
7. **Test framework:** `unittest` (ตรงคำสั่งในเอกสาร Lab) — ไม่ใช้ pytest เพิ่ม dependency
8. **เกณฑ์ VCE_SAT = 0.2 V** เป็นค่าประมาณที่ระบุใน UI/docs ว่าเป็นเกณฑ์เตือน ไม่ใช่ SPICE
9. **โมเดลการทำงาน (จากเอกสาร Lab ขั้น 70–145 นาที):** AI Agent เป็นผู้พัฒนาตามแผนแบบ TDD ทีละ task ส่วนนักศึกษา **ตรวจ Diff/ผลรันทุก task** และเป็นผู้ **Commit ผ่าน GitHub Desktop เอง** ที่ checkpoint ที่กำหนด (ไม่มีการ commit อัตโนมัติจาก Agent) — ตอนเข้าสู่ขั้น Execute, workflow จะเสนอให้เลือกวิธี (Subagent-driven หรือ Native) ตามที่เครื่องมือรองรับ
10. **เนื้อหา `AGENTS.md` (กติกาที่นักศึกษากำหนดเอง):** หลักการสูงสุดคือ **AI ต้องถามนักศึกษาก่อนทำทุกครั้ง และรายงานผลทุกครั้งที่แก้ไขตามสิ่งที่ถูกถาม** — ระดับการถามกำหนดเป็น **ต่อ 1 task ในแผน**: Agent เสนอสิ่งที่จะทำใน task นั้น → ถาม 1 ครั้ง → ทำงาน → รายงานผล + ผล test ก่อนไป task ถัดไป เพิ่มเติม: `dc_bias.py` ต้องไม่ import flask, ต้องมี test ผ่านก่อน commit, นักศึกษาเป็นคน Commit ผ่าน GitHub Desktop เท่านั้น, ห้าม commit `.venv/`/`__pycache__/`/secrets, ขอบเขตยึดตาม Design Note นี้ การเพิ่มขอบเขตต้องถามก่อนเสมอ

## 8. โครงสร้างไฟล์และความรับผิดชอบ

```
BJT-DC-Bias-Web-App/
├── app.py                  # Flask routes: GET / , POST /calculate + แปลงหน่วย + จัด error
├── dc_bias.py              # สมการวิศวกรรมล้วน (SI) + BiasError + region/warnings — ไม่ import flask
├── templates/index.html    # ฟอร์ม + ตารางผล + บล็อก error/warning (Jinja2, ไทย)
├── static/style.css        # จัดหน้า การ์ด ตาราง สี warning/error
├── tests/test_dc_bias.py   # unit tests คณิตศาสตร์ + validation + region
├── tests/test_web.py       # Flask test client: GET / , POST valid/invalid
├── requirements.txt        # flask
├── README.md               # วิธี venv/รัน/ทดสอบ (ตามคำสั่งในเอกสาร Lab)
├── AGENTS.md               # ข้อตกลงการทำงานกับ AI
├── .gitignore              # Python: .venv/, __pycache__/, .env ฯลฯ
└── docs/
    ├── design-note.md      # เอกสารนี้
    ├── validation.md       # การคำนวณอิสระ + ตารางเทียบผลจากเว็บ/tests
    └── reflection.md       # สะท้อนคิดหลังจบ Lab (นักศึกษาเติมเอง)
```

## 9. Interface — `dc_bias.py`

```python
class BiasError(ValueError):
    """ค่าอุปกรณ์ไม่สมเหตุสมผล (R≤0, β≤0, VCC≤0, VBE<0) — มี .field บอกฟิลด์ที่ผิด"""

def calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe) -> dict:
    """อินพุต SI ทั้งหมด (V, Ω, ค่าลิ้น)
    คืน dict:
      vth, rth          # V, Ω  (ค่า Thevenin ที่ขา Base)
      ib, ic, ie        # A    (ไฟไบแอสสามขั้ว)
      vb, ve, vc, vce   # V    (จุดทำงาน DC)
      region            # "forward-active" | "cutoff" | "saturation"
      warnings          # list[str] — ข้อจำกัดของแบบจำลอง (ภาษาไทย)
    raise BiasError เมื่ออินพุตผิดกายภาพ
    """
```

## 10. ผลอ้างอิงจากการคำนวณอิสระ (เทียบใน tests + docs/validation.md)

| ปริมาณ | ค่า (ตรวจสอบแล้ว) | หมายเหตุ |
|---|---|---|
| VTH | 2.16393 V | 12 × 22/122 |
| RTH | 18.0328 kΩ | 100k∥22k |
| IB | 12.2986 µA | (2.16393−0.70)/119.033 kΩ |
| IC | 1.22986 mA | β·IB (แสดง 4 ทศนิยม: 1.2299) |
| IE | 1.24216 mA | (β+1)·IB |
| VE | 1.24216 V | IE·RE |
| VB | 1.94216 V | VE+VBE |
| VC | 9.29431 V | 12 − IC·2.2k |
| VCE | 8.05216 V (แสดง: 8.0522) | VC−VE → **Forward-Active** ✅ |

*ค่าข้างต้นตรวจสอบด้วยเลขคณิตเศษส่วนแท้: IB = 54473/4429210000 A — เดิม (รอบแรก) ปัดเลขผิดที่ตำแหน่งที่ 4–5 ทศนิยม*

เคสทดสอบ region: **Cutoff** — R2=5 kΩ (VTH=0.571 V < 0.70 V); **Saturation** — RC=10 kΩ (VCE ติดลบตามสูตร) → ต้องขึ้น warning ทั้งสองเคส

## 11. แผน Tests (map กับ Acceptance A1–A7)

**tests/test_dc_bias.py (unit, ≥3):** ชุดอ้างอิงตรงมือ · สมการสัมพันธ์ IE=(β+1)IB · Cutoff warning · Saturation warning · BiasError เมื่อ R≤0 / β≤0 / VCC≤0
**tests/test_web.py (Flask test client, ≥3):** GET / → 200 มีฟอร์ม · POST /calculate ชุดอ้างอิง → 200 + ค่า VCE/IC ตรงมือ (ไม่ใช่ hardcode) · POST ค่าผิด (ติดลบ/ตัวหนังสือ) → ข้อความ error โดยไม่ crash

## 12. สิ่งที่เหลือให้ผู้สร้างตัดสินใจ (Builder calls)

- รายละเอียด CSS (สี/ฟอนต์) และ layout ของการ์ด — ไม่บังคับตามภาพในเอกสาร Lab
- จำนวนทศนิยมที่แสดง (แนะนำ 4 ตัวสำหรับ V/A, ปัดหน่วยให้อ่านง่าย)
- ข้อความ error/warning ภาษาไทยฉบับจริง (เทียบเจตนาในหัวข้อ 7)

## 13. เกณฑ์ตรวจรับ (จากเอกสาร Lab หัวข้อ 09) และสิ่งที่ต้องส่ง

**Acceptance ใน Browser (A1–A7):** A1 GET / 200 มีฟอร์ม · A2 POST คำนวณจริง (ไม่ hardcode) · A3 ตรงค่าอิสระ · A4 error ไม่ crash · A5 warning region · A6 ≥3 unit + ≥1 HTTP tests · A7 clone แล้วทำตาม README ได้ — ทั้งหมดต้องผ่านก่อนจบคาบ พร้อม commit ผ่าน GitHub Desktop และ **Publish repo ขึ้น GitHub**

**ชุดส่ง Moodle (จากเอกสาร Lab หัวข้อ 10):** Repository URL + Commit SHA ล่าสุด · ไฟล์ครบทั้ง server/templates/CSS/logic/tests/README · **ภาพหน้าจอ** เว็บคำนวณสำเร็จ + กรณี error · **Test Log** · `docs/reflection.md` (นักศึกษาเติมคำตอบรายบุคคล: ทำไมเปิด index.html ตรง ๆ ไม่เท่ากับรัน Flask, ฟอร์มส่งข้อมูลไป Python อย่างไร ฯลฯ) — การเปิดดูจาก repo อย่างเดียวไม่พอ ต้องรันผ่าน Python Server ตาม README

**ทุก checkpoint การทำงาน (commit):** นักศึกษาตรวจ diff ใน GitHub Desktop → เขียน Summary → Commit to main → ตอนท้าย Push + ส่ง SHA
