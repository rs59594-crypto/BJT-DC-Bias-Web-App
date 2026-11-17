# BJT DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **กติกาเฉพาะของ repo นี้ (จาก AGENTS.md/design §7.10):** ก่อนเริ่มแต่ละ task ต้องถามนักศึกษาก่อน 1 ครั้ง และรายงานผล + ผล test หลังทำเสร็จทุก task การ commit ทำโดยนักศึกษาผ่าน GitHub Desktop เท่านั้น (ไม่ใช้ git CLI)

**Goal:** Flask web app หลายไฟล์ที่คำนวณ DC bias ของ BJT Common-Emitter Voltage-Divider จากฟอร์มบนเว็บ แสดงผลพร้อมหน่วย + validation + region warnings

**Architecture:** `dc_bias.py` เก็บสมการวิศวกรรมล้วน (SI units, ไม่ import flask) → `app.py` แปลงหน่วย kΩ→Ω เรียกคำนวณ แล้ว render `templates/index.html` ด้วย Jinja2, CSS แยกที่ `static/style.css`, tests แยกชั้นวิศวกรรม/HTTP

**Tech Stack:** Python 3.14, Flask 3.1 (dependency เดียวใน requirements.txt), unittest (ตามคำสั่งในเอกสาร Lab — ไม่ใช้ pytest)

**Spec:** `docs/design-note.md` (ทุกค่าอ้างอิง/สมการ/เกณฑ์ A1–A7 ระบุที่นั่น)

## Global Constraints

- UI ภาษาไทยเป็นหลัก สัญลักษณ์วิศวกรรมอังกฤษ (VB, IC, kΩ)
- `dc_bias.py` ห้าม import flask หรือรู้จัก HTML/HTTP
- หน่วยภายใน `dc_bias.py`: SI ล้วน (V, Ω, A) — แปลง A→mA/µA เฉพาะชั้นแสดงผลใน `app.py`
- ฟอร์มกรอก R เป็น kΩ (default 100, 22, 2.2, 1) → ×1000 ใน `app.py`
- เกณฑ์ region: `VTH ≤ VBE` → cutoff; `VCE < 0.2` V → saturation; ทั้งสองกรณีแสดงค่าที่คำนวณได้พร้อม warning
- Validation → `BiasError(ValueError)` มี `.field` (R≤0, β≤0, VCC≤0, VBE<0) — หน้าเว็บต้องได้ HTTP 200 + ข้อความไทย ไม่ crash
- ชุดอ้างอิง: VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k, β=100, VBE=0.70 → IC=1.2298 mA, VCE=8.0523 V, region=forward-active
- รัน: `python -m flask --app app run --debug` · ทดสอบ: `python -m unittest discover -s tests -v`
- ห้าม commit `.venv/`, `__pycache__/`, `.env`

## Review Focus

ห้า input class ที่ spec บอกเป็นนัยแต่ต้อง pin ด้วย test (ระบุ task เจ้าของ):

1. **กรอกตัวหนังสือแทนตัวเลข** (`vcc="abc"`) → 200 + error ไทย ไม่ 500 → test ใน Task 3
2. **ฟิลด์ว่าง/ขาดหายใน POST** → 200 + error ไทย ไม่ KeyError → test ใน Task 3
3. **VBE ติดลบ** → `BiasError` ไม่ใช่ผลลัพธ์แปลก ๆ → test ใน Task 2
4. **ขอบเขต region ที่ VCE = 0.2 V เป๊ะ** → ยังเป็น forward-active (ใช้ `<` เท่านั้น) → test ใน Task 2
5. **ค่าใหญ่ผิดปกติแต่ valid** (β=10000) → คำนวณได้ค่า finite ไม่ crash → test ใน Task 2

---

### Task 1: Project Scaffold

**Files:**
- Create: `.gitignore`, `requirements.txt`, `README.md`, `AGENTS.md`, `tests/__init__.py`

**Interfaces:**
- Produces: โครง repo ตาม design §8 + README วิธี venv/รัน/ทดสอบ (A7) + AGENTS.md กติกาจาก design §7.10

- [ ] **Step 1: สร้าง `.gitignore`** — เนื้อหา Python มาตรฐาน: `.venv/`, `__pycache__/`, `*.pyc`, `.env`, `instance/`

- [ ] **Step 2: สร้าง `requirements.txt`** — บรรทัดเดียว `flask` (ไม่ล็อกเวอร์ชันราย minor เพื่อให้ clone ลง Python ใหม่ได้)

- [ ] **Step 3: สร้าง `README.md`** (ไทย): คำอธิบายโปรเจกต์ 1 ย่อหน้า + บล็อกคำสั่งตามเอกสาร Lab ขั้นที่ 4:
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1        # Linux/macOS: source .venv/bin/activate
  python -m pip install -r requirements.txt
  python -m flask --app app run --debug   # เปิด http://127.0.0.1:5000/
  python -m unittest discover -s tests -v
  ```
  พร้อมสมการ/สมมติฐาน Forward-Active + เกณฑ์ VCE_SAT=0.2 V อ้าง design-note.md

- [ ] **Step 4: สร้าง `AGENTS.md`** (ไทย, สั้น): กติกาจาก design §7.10 — ถามก่อนทำทุก task + รายงานผลทุกครั้ง, `dc_bias.py` ห้าม import flask, test ผ่านก่อน commit, นักศึกษา commit ผ่าน GitHub Desktop เท่านั้น, ห้าม commit secrets/`.venv`, เพิ่มขอบเขตต้องถามก่อน

- [ ] **Step 5: สร้าง `tests/__init__.py`** (ไฟล์เปล่า — ให้ unittest discover นำเข้า module ได้เสถียร)

- [ ] **Step 6: ตรวจ** — `Get-ChildItem -Recurse -File` เห็นครบ 5 ไฟล์ตาม design §8 ที่ยังไม่มี

- [ ] **Step 7: Checkpoint — นักศึกษา commit ผ่าน GitHub Desktop** (Summary: `Scaffold project: gitignore, requirements, README, AGENTS`)

### Task 2: Engineering Module `dc_bias.py`

**Files:**
- Create: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Produces (ใช้โดย Task 3):
  - `class BiasError(ValueError)` — มี attribute `.field: str`
  - `def calculate_dc_bias(vcc: float, r1: float, r2: float, rc: float, re: float, beta: float, vbe: float) -> dict`
  - คืน dict keys: `vth, rth, ib, ic, ie, vb, ve, vc, vce, region, warnings` (V, Ω, A, str, list[str])

- [ ] **Step 1: เขียน failing tests** — `tests/test_dc_bias.py` (unittest.TestCase) 11 tests:
  - `test_reference_case`: ชุดอ้างอิง → `assertAlmostEqual(ic, 1.229858e-3, delta=1e-7)`, `vce, 8.052155, delta=1e-5`, `vb, 1.942157`, `ve, 1.242157`, `vc, 9.294312` (delta=1e-5), `region == "forward-active"`, `warnings == []`
  - `test_ie_relation`: `ie ≈ (beta+1)*ib` และ `ic ≈ beta*ib`
  - `test_thevenin`: `vth ≈ 2.163934`, `rth ≈ 18032.7869` (delta=1e-3)
  - `test_cutoff_region`: R2=5 kΩ (VTH=0.5714 < 0.7) → `region == "cutoff"`, `len(warnings) >= 1`
  - `test_saturation_region`: RC=10 kΩ (VCE ติดลบ) → `region == "saturation"`, warning present
  - `test_region_boundary_near_vce_02`: RC=8584 Ω → VCE≈0.2007 → `forward-active`; RC=8590 Ω → VCE≈0.1934 → `saturation` (pin ขอบเขตที่ 0.2 V, ใช้ `<` เท่านั้น)
  - `test_negative_vbe_raises`: `vbe=-0.7` → `BiasError` ที่ `.field == "vbe"`
  - `test_zero_resistor_raises`: `r1=0` → `BiasError`; `rc=-100` → `BiasError`
  - `test_invalid_beta_raises`: `beta=0`, `beta=-5` → `BiasError`
  - `test_invalid_vcc_raises`: `vcc=0`, `vcc=-9` → `BiasError`
  - `test_large_beta_still_finite`: `beta=10000` → ทุกค่า finite (`math.isfinite`)

- [ ] **Step 2: รันยืนยัน fail** — `python -m unittest discover -s tests -v` → ModuleNotFoundError: dc_bias

- [ ] **Step 3: Implement `dc_bias.py`** — `BiasError(ValueError)` (init รับ `field` + ข้อความไทย) แล้ว `calculate_dc_bias`: validate ทีละฟิลด์ → สมการ design §5 ตรงตัว → region/warnings ตาม Global Constraints → คืน dict ตาม Interfaces (พารามิเตอร์ชื่อ `re` ตรง design §9 — โมดูลนี้ห้าม `import re`)

- [ ] **Step 4: รันยืนยัน pass** — `python -m unittest discover -s tests -v` → 11/11 OK

- [ ] **Step 5: Checkpoint — นักศึกษา commit ผ่าน GitHub Desktop** (Summary: `Add dc_bias engineering module with unit tests`)

### Task 3: Flask App + Template + CSS

**Files:**
- Create: `app.py`, `templates/index.html`, `static/style.css`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `calculate_dc_bias(vcc, r1, r2, rc, re_, beta, vbe) -> dict`, `BiasError` (จาก Task 2)
- Produces: Flask app ที่ `GET /` + `POST /calculate` render ผลในหน้าเดียว

- [ ] **Step 1: เขียน failing tests** — `tests/test_web.py` ใช้ `app.test_client()` 7 tests:
  - `test_get_index_200`: GET `/` → 200, `b'name="vcc"'` และ `Calculate` อยู่ในหน้า
  - `test_post_reference_results`: POST `/calculate` ฟิลด์ `vcc=12, r1=100, r2=22, rc=2.2, re=1, beta=100, vbe=0.7` (kΩ) → 200, `b"8.0522"` (VCE) และ `b"1.2299"` (IC mA)
  - `test_post_cutoff_warning`: POST `r2=5` → 200 + คำว่า `Cutoff` ในหน้า
  - `test_post_saturation_warning`: POST `rc=10` → 200 + `Saturation`
  - `test_post_negative_vcc_error`: POST `vcc=-5` → 200 + `error` CSS class หรือข้อความไทย ไม่ใช่ 500
  - `test_post_non_numeric_error`: POST `vcc=abc` → 200 + error ไม่ใช่ 500 (Review Focus #1)
  - `test_post_missing_field_error`: POST ไม่ส่ง `beta` → 200 + error ไม่ใช่ 500 (Review Focus #2)

- [ ] **Step 2: รันยืนยัน fail** — `python -m unittest discover -s tests -v` → 7 tests ERROR (no module app)

- [ ] **Step 3: Implement `app.py`** — `DEFAULTS` dict (ค่าอ้างอิงหน่วยฟอร์ม) · `parse_form(form) -> dict SI` (แปลง kΩ→Ω, `float()` ค่าผิด/ขาด → `BiasError` ข้อความไทย) · `GET /` render defaults · `POST /calculate` try parse+calculate → render results (แปลง `ic*1000`→mA, `ib*1e6`→µA, `:.4f`) except BiasError → render ฟอร์มเดิม + error + ค่าที่ผู้ใช้พิมพ์ค้างไว้

- [ ] **Step 4: Implement `templates/index.html` + `static/style.css`** — ไทย, ฟอร์ม 7 ฟิลด์ + ปุ่ม "Calculate DC Bias" + ตารางผล VB/VE/VC/VCE [V], IC [mA], IB [µA], IE [mA] + บล็อก error (ส้ม) / warning (เหลือง) / region badge — ไม่ฝังสมการใน template

- [ ] **Step 5: รันยืนยัน pass** — `python -m unittest discover -s tests -v` → 18/18 OK

- [ ] **Step 6: Checkpoint — นักศึกษา commit ผ่าน GitHub Desktop** (Summary: `Add Flask app, template, CSS and HTTP tests`)

### Task 4: Full Verification + Docs

**Files:**
- Create: `docs/validation.md`
- Modify: none

**Interfaces:**
- Consumes: ทุกอย่างจาก Task 1–3

- [ ] **Step 1: สร้าง `.venv` และติดตั้ง** — `python -m venv .venv` → `.venv\Scripts\python.exe -m pip install -r requirements.txt` (จำลองสิ่งที่ผู้ตรวจทำตาม A7)

- [ ] **Step 2: รัน tests ใน venv** — `.venv\Scripts\python.exe -m unittest discover -s tests -v` → 18 OK (บันทึก log เป็นหลักฐานส่ง Moodle)

- [ ] **Step 3: เริ่ม Flask server (background)** — `.venv\Scripts\python.exe -m flask --app app run --debug` ที่ `127.0.0.1:5000` → ยิง GET `/` + POST `/calculate` ด้วย Invoke-WebRequest ยืนยัน 200 + มีค่าผล → ทิ้งไว้ให้นักศึกษาเปิด browser ทดสอบ/ดึงภาพหน้าจอเอง

- [ ] **Step 4: เขียน `docs/validation.md`** — ตารางค่ามือ vs ผลจากเว็บ vs ผลจาก tests (ทุกค่าตรงกัน) + เคส error/warning ที่ทดสอบ + ข้อจำกัดแบบจำลอง (β คงที่, VBE คงที่, VCE_SAT=0.2 V ประมาณ, ไม่ใช่ ngspice)

- [ ] **Step 5: สร้าง `docs/reflection.md` (stub ให้นักศึกษาเติมคำตอบ)** — 4 คำถามรายบุคคลจากเอกสาร Lab §10: ทำไมเปิด index.html ตรง ๆ ไม่เท่ากับรัน Flask · ฟอร์มส่งข้อมูลไป Python อย่างไร · แก้สมการใน dc_bias.py แล้วต้องแก้ HTML ไหม · ทำไมผลนอก region ต้องมี warning

- [ ] **Step 6: Checkpoint — นักศึกษา commit ผ่าน GitHub Desktop** (Summary: `Add validation and reflection docs; verify full suite in venv`) แล้ว **Publish repository** + Push + ส่ง Moodle (URL + SHA + ภาพหน้าจอ + test log + reflection)
