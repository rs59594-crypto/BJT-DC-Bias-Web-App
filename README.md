# BJT DC Bias Web App — ENG29 2121 Lab 02 (2/2569)

เว็บแอปพลิเคชัน Flask สำหรับคำนวณ **DC Operating Point ของวงจรขยาย NPN Common-Emitter แบบ Voltage-Divider Bias** — ผู้ใช้กรอก `VCC, R1, R2, RC, RE [kΩ], β, VBE [V]` ผ่านฟอร์มบนหน้าเว็บ แล้ว **Python Backend** คำนวณค่า `VB, VE, VC, VCE [V]`, `IC [mA]`, `IB [µA]`, `IE [mA]` ส่งกลับมาแสดงพร้อมหน่วย ตรวจค่าอินพุตที่ผิด และเตือนเมื่อจุดทำงานออกนอก Forward-Active Region (Cutoff/Saturation)

## การติดตั้งและรัน

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1        # Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app run --debug   # เปิด http://127.0.0.1:5000/
```

หมายเหตุ: ต้องรันผ่าน Flask Server เท่านั้น (อย่าเปิด `templates/index.html` ด้วย double-click เพราะการคำนวณเกิดที่ Python Backend ผ่าน HTTP Request ไม่ใช่ในไฟล์ HTML)

## การทดสอบ

```powershell
python -m unittest discover -s tests -v
```

## สมการและสมมติฐาน (Forward-Active Approximation)

| สมการ | หมายเหตุ |
|---|---|
| `VTH = VCC × R2 / (R1+R2)` | แรงดัน Thevenin ที่ขา Base |
| `RTH = R1R2/(R1+R2)` | ความต้านทาน Thevenin |
| `IB = (VTH−VBE)/(RTH+(β+1)RE)` | กระแสเบส |
| `IC = βIB`, `IE = (β+1)IB` | |
| `VE = IE·RE`, `VB = VE+VBE` | |
| `VC = VCC−IC·RC`, `VCE = VC−VE` | |

สมมติฐาน: **β คงที่** และ **VBE คงที่** (ไม่ใช่ SPICE/ngspice) — กรณี `VTH ≤ VBE` ถือเป็น **Cutoff** และกรณี `VCE < 0.2 V` ถือเป็น **Saturation** (เกณฑ์ VCE_SAT = 0.2 V เป็นค่าประมาณเพื่อการเตือน) ทั้งสองกรณีแสดงค่าที่คำนวณได้พร้อมคำเตือนว่าแบบจำลอง Forward-Active ใช้ไม่ได้ ดูรายละเอียดที่ `docs/design-note.md`

หน่วยอินพุตในฟอร์ม: แรงดันเป็น V, ตัวต้านทานเป็น kΩ (โปรแกรมแปลงเป็น Ω ภายในก่อนคำนวณ)

## โครงสร้างโปรเจกต์

```
app.py                  # Flask routes (GET / , POST /calculate) + แปลงหน่วย
dc_bias.py              # สมการวิศวกรรมล้วน (SI: V, Ω, A) — ไม่ import flask
templates/index.html    # ฟอร์ม + ผลลัพธ์ (Jinja2)
static/style.css        # การแสดงผล
tests/                  # unit tests (วิศวกรรม) + HTTP tests (Flask test client)
docs/                   # design-note, validation, reflection
```
