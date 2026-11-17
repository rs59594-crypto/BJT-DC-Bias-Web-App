"""Flask web app — BJT DC Bias Calculator (Lab 02 · ENG29 2121)

หน้าที่ของไฟล์นี้: routing + แปลงหน่วยฟอร์ม (kΩ → Ω) + จัดรูปการแสดงผล
การคำนวณทั้งหมดอยู่ใน dc_bias.py (โมดูลวิศวกรรมล้วน)
"""
from flask import Flask, render_template, request

from dc_bias import BiasError, calculate_dc_bias

app = Flask(__name__)

# ค่า default ของฟอร์ม (หน่วยตามที่ผู้ใช้กรอก: V, kΩ)
DEFAULTS = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
            "re": "1", "beta": "100", "vbe": "0.7"}

# ชื่อฟิลด์ → ข้อความไทย (ใช้ในข้อความ error)
FIELD_LABELS_TH = {
    "vcc": "VCC", "r1": "R1", "r2": "R2", "rc": "RC", "re": "RE",
    "beta": "β (beta)", "vbe": "VBE",
}

REGION_LABELS = {
    "forward-active": "Forward-Active — อยู่ในบริเวณทำงานปกติ",
    "cutoff": "Cutoff — ภาวะตัดต่อ (ไม่มีกระแสไหล)",
    "saturation": "Saturation — ภาวะอิ่มตัว",
}


def parse_form(form):
    """แปลงค่าจากฟอร์ม (V, kΩ) เป็นหน่วย SI (V, Ω) — ค่าผิด/ขาดหาย → BiasError"""
    values = {}
    for name in DEFAULTS:
        raw = (form.get(name) or "").strip()
        if raw == "":
            raise BiasError(name, f"กรุณากรอกค่า {FIELD_LABELS_TH[name]}")
        try:
            number = float(raw)
        except ValueError:
            raise BiasError(
                name,
                f"{FIELD_LABELS_TH[name]} ต้องเป็นตัวเลขเท่านั้น (ได้รับ: \"{raw}\")",
            ) from None
        values[name] = (number * 1000.0 if name in ("r1", "r2", "rc", "re")
                        else number)
    return values


def _fmt(value, decimals=4):
    """จัดรูปตัวเลขสำหรับแสดงผล (ตัด trailing zeros ทิ้งให้อ่านง่าย)"""
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".") or "0"


def render_page(**context):
    """render index.html พร้อมค่า default ที่ยังไม่ได้ระบุใน context"""
    kwargs = dict(values=DEFAULTS, results=None, error=None,
                  warnings=[], region_label=None)
    kwargs.update(context)
    return render_template("index.html", **kwargs)


@app.route("/")
def index():
    """หน้าแรก — ฟอร์มว่างพร้อมค่า default"""
    return render_page()


@app.route("/calculate", methods=["POST"])
def calculate():
    """รับฟอร์ม → คำนวณ → แสดงผลในหน้าเดียว (error ก็ยังตอบ HTTP 200)"""
    values = {name: (request.form.get(name) or "").strip()
              for name in DEFAULTS}
    try:
        si = parse_form(request.form)
        result = calculate_dc_bias(**si)
    except BiasError as exc:
        return render_page(values=values,
                           error=f"{FIELD_LABELS_TH.get(exc.field, exc.field)}: {exc}")

    display = {
        "vth": _fmt(result["vth"]),
        "rth": _fmt(result["rth"] / 1000.0),          # Ω → kΩ
        "ib": _fmt(result["ib"] * 1e6),               # A → µA
        "ic": _fmt(result["ic"] * 1e3),               # A → mA
        "ie": _fmt(result["ie"] * 1e3),               # A → mA
        "vb": _fmt(result["vb"]),
        "ve": _fmt(result["ve"]),
        "vc": _fmt(result["vc"]),
        "vce": _fmt(result["vce"]),
    }
    return render_page(values=values, results=display,
                       warnings=result["warnings"],
                       region_label=REGION_LABELS[result["region"]])


if __name__ == "__main__":
    app.run(debug=True)
