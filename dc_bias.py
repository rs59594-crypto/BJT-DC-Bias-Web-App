"""โมดูลวิศวกรรมล้วนสำหรับคำนวณ DC Operating Point
ของวงจรขยาย NPN Common-Emitter แบบ Voltage-Divider Bias

- หน่วยภายใน: SI เท่านั้น (แรงดัน V, ความต้านทาน Ω, กระแส A)
- โมดูลนี้ไม่รู้จัก Flask/HTML/HTTP ใด ๆ (ดู AGENTS.md กติกา 2)
- สมการและสมมติฐานอ้าง docs/design-note.md §5

สมมติฐาน Forward-Active Approximation: β คงที่, VBE คงที่
เกณฑ์ region: VTH ≤ VBE → cutoff (ตรวจก่อน) · VCE < 0.2 V → saturation
"""

import math

# แรงดันอิ่มตัวโดยประมาณที่ใช้เป็นเกณฑ์เตือน (V)
VCE_SAT_WARN = 0.2


class BiasError(ValueError):
    """ความผิดพลาดจากอินพุตที่ไม่ถูกต้อง (ใช้ในชั้นแสดงผลแสดงข้อความไทย)"""

    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field


def _validate_positive(name: str, value: float, label_th: str) -> float:
    """ตรวจว่าค่าต้องเป็นจำนวนจริงมากกว่าศูนย์"""
    if not math.isfinite(value) or value <= 0:
        raise BiasError(name, f"{label_th} ต้องเป็นจำนวนบวกมากกว่า 0 (ได้รับ: {value:g})")
    return value


def _validate_nonnegative(name: str, value: float, label_th: str) -> float:
    """ตรวจว่าค่าต้องเป็นจำนวนจริงตั้งแต่ศูนย์ขึ้นไป"""
    if not math.isfinite(value) or value < 0:
        raise BiasError(name, f"{label_th} ต้องเป็น 0 หรือจำนวนบวกเท่านั้น (ได้รับ: {value:g})")
    return value


def calculate_dc_bias(vcc: float, r1: float, r2: float, rc: float,
                      re: float, beta: float, vbe: float) -> dict:
    """คำนวณจุดทำงาน DC ของวงจร (หน่วย SI: V, Ω, A)

    พารามิเตอร์:
        vcc  : แรงดันแหล่งจ่าย [V] (> 0)
        r1   : ตัวต้านทาน R1 ของ voltage divider [Ω] (> 0)
        r2   : ตัวต้านทาน R2 ของ voltage divider [Ω] (> 0)
        rc   : ตัวต้านทาน collector [Ω] (> 0)
        re   : ตัวต้านทาน emitter [Ω] (> 0)
        beta : อัตราขยายกระแส DC ของทรานซิสเตอร์ (> 0)
        vbe  : แรงดัน base-emitter [V] (≥ 0)

    คืน dict: vth, rth, ib, ic, ie, vb, ve, vc, vce, region, warnings
    อาจ raise BiasError เมื่ออินพุตไม่ถูกต้อง
    """
    # ---- validation (ทีละฟิลด์) ----
    vcc = _validate_positive("vcc", vcc, "VCC")
    r1 = _validate_positive("r1", r1, "R1")
    r2 = _validate_positive("r2", r2, "R2")
    rc = _validate_positive("rc", rc, "RC")
    re = _validate_positive("re", re, "RE")
    beta = _validate_positive("beta", beta, "β (beta)")
    vbe = _validate_nonnegative("vbe", vbe, "VBE")

    # ---- Thevenin ที่ขา base (สมการ design §5 ตรงตัว) ----
    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)

    # ---- กระแสตามแบบจำลอง Forward-Active ----
    # IB = (VTH - VBE) / (RTH + (β+1)·RE)
    denominator = rth + (beta + 1.0) * re
    ib = (vth - vbe) / denominator
    ic = beta * ib
    ie = (beta + 1.0) * ib

    # ---- แรงดันที่ขาต่าง ๆ ----
    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    # ---- region + warnings (ตรวจ cutoff ก่อน saturation) ----
    warnings: list[str] = []
    if vth <= vbe:
        region = "cutoff"
        warnings.append(
            "VTH ≤ VBE — ทรานซิสเตอร์อยู่ในภาวะ Cutoff ไม่มีกระแสไหล "
            "ค่าที่แสดงเป็นผลจากแบบจำลองเชิงเส้นซึ่งใช้ไม่ได้จริงในภาวะนี้"
        )
    elif vce < VCE_SAT_WARN:
        region = "saturation"
        warnings.append(
            f"VCE < {VCE_SAT_WARN} V — ทรานซิสเตอร์เข้าใกล้/อยู่ในภาวะ Saturation "
            "ค่าที่แสดงเป็นผลจากแบบจำลอง Forward-Active ซึ่งใช้ไม่ได้จริงในภาวะนี้"
        )
    else:
        region = "forward-active"

    return {
        "vth": vth,
        "rth": rth,
        "ib": ib,
        "ic": ic,
        "ie": ie,
        "vb": vb,
        "ve": ve,
        "vc": vc,
        "vce": vce,
        "region": region,
        "warnings": warnings,
    }
