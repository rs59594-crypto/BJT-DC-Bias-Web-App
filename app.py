"""Flask web app — BJT DC Bias Calculator (Lab 02 → Lab 03)

หน้าที่ของไฟล์นี้: routing + เลือกวงจรตามโหมด + แปลงหน่วยฟอร์ม (kΩ → Ω) + จัดรูปการแสดงผล
การคำนวณทั้งหมดอยู่ใน dc_bias.py (โมดูลวิศวกรรมล้วน)

โหมดวงจร (Lab 03): divider (เดิม) | fixed — ต่อมา: emitter
- POST ที่ไม่มีฟิลด์ mode เลย (form ของ Lab 2 / tests เดิม) → ใช้ divider (ย้อนรุ่น)
- POST ที่มี mode แต่ค่าไม่รู้จัก → ข้อความผิดพลาด ไม่เดาเป็น Divider
"""
from flask import Flask, render_template, request

from dc_bias import (BiasError, calculate_dc_bias, calculate_emitter_bias,
                     calculate_fixed_bias)

app = Flask(__name__)

# โหมดวงจร: ชื่อ → label ไทย + รายชื่อฟิลด์ที่โหมดนั้นต้องใช้
MODES = {
    "divider": {"label": "Voltage Divider Bias",
                "fields": ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")},
    "fixed": {"label": "Fixed Bias",
              "fields": ("vcc", "rb", "rc", "beta", "vbe")},
    "emitter": {"label": "Emitter Bias",
                "fields": ("vcc", "rb", "rc", "re", "beta", "vbe")},
}

# ค่า default ของฟอร์ม (หน่วยตามที่ผู้ใช้กรอก: V, kΩ — RB = 1000 kΩ = 1 MΩ)
DEFAULTS = {"vcc": "12", "r1": "100", "r2": "22", "rc": "2.2",
            "re": "1", "rb": "1000", "beta": "100", "vbe": "0.7"}

# ชื่อฟิลด์ → (ชื่อวิศวกรรม, คำอธิบายไทย, หน่วยบนฟอร์ม)
FIELD_DEFS = {
    "vcc": ("VCC", "แรงดันแหล่งจ่าย", "V"),
    "r1": ("R1", "ตัวต้านทานบน", "kΩ"),
    "r2": ("R2", "ตัวต้านทานล่าง", "kΩ"),
    "rc": ("RC", "ตัวต้านทาน Collector", "kΩ"),
    "re": ("RE", "ตัวต้านทาน Emitter", "kΩ"),
    "rb": ("RB", "ตัวต้านทาน Base", "kΩ"),
    "beta": ("β (beta)", "อัตราขยายกระแส", ""),
    "vbe": ("VBE", "แรงดัน Base-Emitter", "V"),
}

# ชื่อฟิลด์ → ข้อความไทย (ใช้ในข้อความ error)
FIELD_LABELS_TH = {name: eng for name, (eng, _th, _unit) in FIELD_DEFS.items()}

REGION_LABELS = {
    "forward-active": "Forward-Active — อยู่ในบริเวณทำงานปกติ",
    "cutoff": "Cutoff — ภาวะตัดต่อ (ไม่มีกระแสไหล)",
    "saturation": "Saturation — ภาวะอิ่มตัว",
}


def _resolve_mode(raw):
    """แปลงค่า mode จากฟอร์ม: ไม่ส่งมา → divider (ย้อนรุ่น), ส่งมาผิด → BiasError"""
    mode = (raw or "").strip()
    if mode == "":
        return "divider"
    if mode not in MODES:
        raise BiasError(
            "mode",
            f"โหมดวงจร \"{mode}\" ไม่ถูกต้อง — เลือกได้จากเมนูเท่านั้น",
        )
    return mode


def parse_form(form, mode):
    """แปลงค่าจากฟอร์ม (V, kΩ) เป็นหน่วย SI (V, Ω) — ตรวจเฉพาะช่องที่โหมดต้องใช้"""
    values = {}
    for name in MODES[mode]["fields"]:
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
        values[name] = (number * 1000.0 if name in ("r1", "r2", "rc", "re", "rb")
                        else number)
    return values


def _fmt(value, decimals=4):
    """จัดรูปตัวเลขสำหรับแสดงผล (ตัด trailing zeros ทิ้งให้อ่านง่าย)"""
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".") or "0"


def render_page(**context):
    """render index.html พร้อมค่า default ที่ยังไม่ได้ระบุใน context"""
    kwargs = dict(values=DEFAULTS, results=None, error=None,
                  warnings=[], region_label=None, mode="divider",
                  mode_label=MODES["divider"]["label"],
                  modes=MODES, FIELD_DEFS=FIELD_DEFS)
    kwargs.update(context)
    return render_template("index.html", **kwargs)


@app.route("/")
def index():
    """หน้าแรก — ฟอร์มตามโหมดที่เลือก (default: divider)"""
    try:
        mode = _resolve_mode(request.args.get("mode"))
    except BiasError as exc:
        return render_page(error=f"โหมดวงจร: {exc}")
    return render_page(mode=mode, mode_label=MODES[mode]["label"])


@app.route("/calculate", methods=["POST"])
def calculate():
    """รับฟอร์ม → เลือกฟังก์ชันตามโหมด → คำนวณ → แสดงผลในหน้าเดียว

    error ทุกกรณีตอบ HTTP 200 + ข้อความไทย และไม่แสดงผลลัพธ์รอบก่อน
    (results ถูกตั้งเป็น None เสมอใน error path — เคส A5)
    """
    values = {name: (request.form.get(name) or "").strip()
              for name in DEFAULTS}
    try:
        mode = _resolve_mode(request.form.get("mode"))
        si = parse_form(request.form, mode)
        if mode == "divider":
            result = calculate_dc_bias(**si)
        elif mode == "fixed":
            result = calculate_fixed_bias(**si)
        elif mode == "emitter":
            result = calculate_emitter_bias(**si)
        else:  # กันพลาดเชิงโครงสร้าง — โหมดที่ _resolve_mode ไม่รู้จักหลุดมาไม่ได้
            raise BiasError("mode", f"โหมดวงจร \"{mode}\" ยังไม่รองรับ")
    except BiasError as exc:
        return render_page(values=values,
                           error=f"{FIELD_LABELS_TH.get(exc.field, exc.field)}: {exc}")

    display = {
        "ib": _fmt(result["ib"] * 1e6),               # A → µA
        "ic": _fmt(result["ic"] * 1e3),               # A → mA
        "ie": _fmt(result["ie"] * 1e3),               # A → mA
        "vb": _fmt(result["vb"]),
        "ve": _fmt(result["ve"]),
        "vc": _fmt(result["vc"]),
        "vce": _fmt(result["vce"]),
    }
    if "vth" in result:                                # เฉพาะ Divider
        display["vth"] = _fmt(result["vth"])
        display["rth"] = _fmt(result["rth"] / 1000.0)  # Ω → kΩ
    return render_page(values=values, mode=mode,
                       mode_label=MODES[mode]["label"],
                       results=display,
                       warnings=result["warnings"],
                       region_label=REGION_LABELS[result["region"]])


if __name__ == "__main__":
    app.run(debug=True)
