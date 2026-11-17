# Lab 03 Implementation Plan — Multi-Mode BJT DC Bias + Browser Acceptance

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (native) — ทำ task-by-task ตามกติกา AGENTS.md: ถามนักศึกษาก่อนเริ่มทุก task 1 ครั้ง และรายงานผล + ผล test หลังเสร็จ · นักศึกษา commit ผ่าน GitHub Desktop เท่านั้น
>
> **Spec:** `docs/superpowers/specs/2026-11-17-lab03-multi-mode-bias-design.md` · **Source of truth:** เอกสาร Lab 03 §03–§07

**Goal:** เว็บ Flask เดิมเลือกวงจรได้ 3 แบบ (Divider คงผลเดิม + Fixed + Emitter) และตรวจรับ A1–A5 ผ่าน Playwright MCP

**Rulings จากนักศึกษา:**
- ตรวจ Browser ด้วย **Playwright MCP ตามเส้นทางหลักของ Lab** (Node.js กำลังติดตั้ง — task สุดท้ายรอเรื่องนี้)
- **ไม่สร้าง unittest ใหม่** — tests เดิม 18 ตัวต้องผ่านทุก task (กัน Divider เสีย)

**Global Constraints**
- `dc_bias.py` ห้าม import flask · SI ภายใน (V, Ω, A) · ฟอร์ม kΩ (RB = 1 MΩ = 1000 kΩ)
- Divider (`calculate_dc_bias`) **ห้ามแก้แม้แต่บรรทัดเดียว**
- อินพุตผิด → HTTP 200 + ข้อความไทย ไม่ 500 · โหมดไม่รู้จัก → error ชัดเจน
- รัน test: `python -m unittest discover -s tests -v` (ครบ 18 ต้อง OK ทุก task)

## ข้อตกลงเรื่อง mode ที่ขาดหาย (สำคัญ — เพื่อให้ tests เดิมผ่าน)

POST ที่ **ไม่มีฟิลด์ `mode` เลย** (เช่น form ของ Lab 2 / tests เดิม) → ใช้ `divider` (ย้อนรุ่น compatible) · POST ที่มี `mode` **แต่ค่าไม่อยู่ใน 3 โหมด** (เช่น `mode=junk`) → error ชัดเจน **ไม่เดาเป็น Divider** — ตรงข้อความ Lab "โหมดที่ไม่รู้จักต้องแจ้งข้อผิดพลาด" โดยไม่ทำ tests เดิมเสีย

---

### Task 1: ฟังก์ชัน Fixed และ Emitter ใน `dc_bias.py`

**Files:** Modify: `dc_bias.py` (เพิ่ม 2 ฟังก์ชัน — ไม่แตะ `calculate_dc_bias`)

**Interfaces (ใช้โดย Task 2):**
- `calculate_fixed_bias(vcc, rb, rc, beta, vbe) -> dict` — keys: `ib, ic, ie, vb, ve, vc, vce, region, warnings` (ไม่มี vth/rth) · IB = (VCC−VBE)/RB · VE = 0.0
- `calculate_emitter_bias(vcc, rb, rc, re, beta, vbe) -> dict` — keys เดียวกัน · IB = (VCC−VBE)/[RB+(β+1)RE] · VE = IE·RE
- validation ทั้งคู่: `vcc>0, rb>0, rc>0, beta>0` (`_validate_positive`), `re>0` (เฉพาะ Emitter), `vbe≥0` (`_validate_nonnegative`) — RB ≤ 0 → `BiasError("rb", ...)`
- region โหมดใหม่ (ตาม Lab §03): `IB ≤ 0` → `"cutoff"` + warning · ไม่งั้น `VCE ≤ 0.2` → `"saturation"` + warning · ไม่งั้น `"forward-active"` + warnings ว่าง

- [ ] Step 1: เพิ่ม 2 ฟังก์ชัน (reuse `_validate_*`, โครง dict ตาม Interfaces)
- [ ] Step 2: รัน tests → 18/18 OK (ต้องไม่แตะ Divider)
- [ ] Step 3: ตรวจมือด้วย `python -c` ค่าที่นักศึกษาจะใช้เทียบทีหลัง **ห้ามยึดเป็นค่าคาดหมาย** (ค่าคาดหมายเป็นของนักศึกษา) — แค่ยืนยัน finite และค่าสมเหตุสมผล (เช่น Fixed RB=1M: IB ราว 11 µA ระดับ)
- [ ] Step 4: Checkpoint — commit ผ่าน GitHub Desktop (Summary: `Add fixed and emitter bias functions to dc_bias module`)

### Task 2: เลือกโหมดใน `app.py`

**Files:** Modify: `app.py`

**Interfaces:**
- `MODES` dict: `{"divider": {"label": "Voltage Divider Bias", "fields": [...]}, "fixed": {...}, "emitter": {...}}` — fields ต่อโหมด: divider=`vcc,r1,r2,rc,re,beta,vbe` · fixed=`vcc,rb,rc,beta,vbe` · emitter=`vcc,rb,rc,re,beta,vbe`
- `parse_form(form, mode) -> dict SI`: mode ไม่อยู่ใน MODES (เมื่อ "มีค่าแต่ไม่รู้จัก") → `BiasError("mode", "โหมดวงจรไม่ถูกต้อง...")` · ตรวจเฉพาะ fields ของโหมด (ค่าขาด/ว่าง/ไม่ใช่ตัวเลข → BiasError ไทยต่อฟิลด์) · R ทุกชนิด (rb ด้วย) ×1000
- GET `/`: อ่าน `?mode=` (ค่าไม่รู้จัก → แสดงฟอร์ม divider + ข้อความ error) · POST `/calculate`: อ่าน `mode` (ไม่มีฟิลด์ → `divider`) · if/elif dispatch: divider→`calculate_dc_bias`, fixed→`calculate_fixed_bias`, emitter→`calculate_emitter_bias` · else → error
- คำนวณแล้ว render พร้อม `mode_label` + ค่า display เดิม (`_fmt`, ic×1000, ib×1e6, rth/1000 เฉพาะ divider) · error path คง `results=None` (A5: ห้ามแสดงผลรอบก่อน)

- [ ] Step 1: แก้ `app.py` ตาม Interfaces (คงโครง render_page เดิม เพิ่ม mode/fields ให้ template)
- [ ] Step 2: รัน tests → **18/18 OK** (tests เดิมไม่ส่ง mode ต้องยังได้ผล Divider เดิม `8.0522`/`1.2299`)
- [ ] Step 3: sanity ด้วย Invoke-WebRequest บน server ที่รันอยู่: POST ตัวอย่าง fixed (vcc=12, rb=1000, rc=2.2, beta=100, vbe=0.7, mode=fixed) → 200 มีค่า · POST `mode=junk` → 200 + ข้อความ error · POST divider ค่าเดิม → `8.0522` เหมือนเดิม
- [ ] Step 4: Checkpoint — commit (Summary: `Select bias mode by circuit type in Flask routes`)

### Task 3: ฟอร์มเลือกโหมด + ผลระบุโหมด

**Files:** Modify: `templates/index.html`, `static/style.css`

- [ ] Step 1: แก้ `index.html`:
  - ฟอร์มเลือกโหมด (เหนือฟอร์มหลัก): `<select name="mode">` 3 ตัวเลือก + ปุ่ม "เปลี่ยนโหมด" — `<form method="get" action="/">` (โหลดใหม่โดยไม่ใช้ JS)
  - ฟอร์มหลัก: `<input type="hidden" name="mode" value="{{ mode }}">` + แสดงเฉพาะช่องของโหมด (Jinja: วนตาม fields ของโหมด — label ไทยต่อฟิลด์: RB/RE หน่วย kΩ) · VCC/RC/β/VBE ใช้ label เดิม
  - บล็อกผล: หัวระบุโหมด ("ผลลัพธ์ · โหมด {{ mode_label }}") + แถว VTH/RTH เฉพาะเมื่อมีคีย์ (divider)
- [ ] Step 2: ปรับ `style.css` เล็กน้อย (สไตล์ select/แถวเลือกโหมด — คงธีมเดิม)
- [ ] Step 3: รัน tests → 18/18 OK · เปิดหน้าใน browser ตรวจตา: dropdown ทำงาน, เปลี่ยนโหมดแล้วช่องเปลี่ยน, ผลระบุโหมดถูก
- [ ] Step 4: Checkpoint — commit (Summary: `Add circuit mode selector to bias form`)

### Task 4: README + ตาราง A1–A5 + ยืนยันครบ

**Files:** Modify: `README.md`, `docs/validation.md`

- [ ] Step 1: README — เพิ่มส่วน "3 โหมดวงจร": ตารางอินพุตต่อโหมด + สมการ IB 3 แบบ + VE ของ Fixed = 0 + วิธีเลือกโหมดบนหน้าเว็บ + หมายเหตุ MCP/Browser ตรวจ A1–A5
- [ ] Step 2: `docs/validation.md` — เพิ่มส่วน "A1–A5 (Lab 03)" เป็นตารางเปล่าคอลัมน์: กรณี | เลือกโหมดและกรอกค่า | คาดหมายก่อนรัน (ของนักศึกษา) | เห็นจริง | วิธีตรวจ | สถานะ | หลักฐาน — ระบุ tolerance: IC ±0.01 mA, VCE ±0.02 V
- [ ] Step 3: รัน tests → 18/18 OK · สแกน git status ให้รู้ไฟล์รอ commit
- [ ] Step 4: Checkpoint — commit (Summary: `Document three bias modes and prepare A1-A5 validation table`)

### Task 5: Playwright MCP + Browser Acceptance A1–A5

**Files:** Modify: `docs/validation.md` (กรอกผลจริง)

- [ ] Step 1: ยืนยัน MCP ทีละชั้นตาม Lab §05: `node --version` ≥ 18 · `npx --version` · รายการ MCP (สถานะ connected) · แล้วให้เอเจนต์เปิด `http://127.0.0.1:5000/` ด้วยเครื่องมือ browser จริง + snapshot บอกชื่อหน้า/ช่อง ≥2 ช่อง — ถ้า MCP ยังไม่พร้อมให้รอ/รายงาน NOT RUN + สลับ OpenCode Browser (ระบุเหตุผล)
- [ ] Step 2: **ขอตารางค่าคาดหมายจากนักศึกษาก่อน** — A2/A3/A4 นักศึกษาคำนวณเองจากสมการ (ห้ามใช้ค่าจากโปรแกรม) + ทำนาย A4 ว่า IC เพิ่ม/ลด เมื่อ RE 2 kΩ พร้อมเหตุผล · A1 ใช้ baseline ที่บันทึกไว้ (IC 1.2299 mA, VCE 8.0522 V)
- [ ] Step 3: รัน A1–A5 ผ่าน Playwright MCP ตามคำสั่งรอบตรวจของ Lab: navigate → snapshot → select mode → fill form → click คำนวณ → snapshot ใหม่อ่านค่า/หน่วย/ข้อความ error · ห้ามใช้ curl/อ่านโค้ดแทน · ห้ามแก้โค้ดก่อนรายงานรอบแรก
- [ ] Step 4: รายงานตาราง: ID | วิธีตรวจ | อินพุต | คาดหมาย | เห็นจริง+หน่วย | PASS/FAIL/NOT RUN | หลักฐาน (ข้อความจากหน้า/screenshot ≥1 กรณี) — ถ้า FAIL รายงานก่อนแล้วค่อยถามแก้ (แก้ทีละจุด + rerun เคสที่เกี่ยวข้อง)
- [ ] Step 5: กรอก `docs/validation.md` · นักศึกษาทวนเอง ≥1 กรณี · Checkpoint — commit (Summary: `Record A1-A5 browser acceptance results`) แล้ว Push + ส่ง Moodle (URL + SHA + ตาราง + ค่าอ้างอิงอิสระ + ระบุส่วนที่ AI ช่วย)

## Review Focus (จุดที่ reviewer ควรเน้น)

1. Divider ต้อง byte-identical เดิม — diff ของ `calculate_dc_bias` ต้องว่าง
2. POST `mode=junk` → error, ไม่คำนวณ Divider เงียบ ๆ
3. Error path ไม่แสดงผลรอบก่อน (A5)
4. RB = 1000 (kΩ) → 1 MΩ แปลงถูกครั้งเดียวที่จุดรับ
5. ค่าคาดหมายทุกตัวในตารางมาจากนักศึกษา ไม่ใช่จากโปรแกรม
