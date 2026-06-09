"""Plantilla PDF + capa de texto/QR (ReportLab + PyPDF). Ajuste coordenadas con ``certificate_reference.pdf``."""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Paragraph

# --- Coordenadas (origen abajo-izquierda, puntos PDF). Plantilla ~842.5 x 595.5 (horizontal). ---
# Ajustar midiendo contra app/templates/certificate_reference.pdf
_LAYOUT = {
    "student_name_y": 305.82,
    "identity_y": 282.20,
    "course_line_y": 258.58,
    "cert_name_y": 232.23,
    "hours_y": 200.60,
    "legal_top_y": 188.0,
    "legal_max_width": 720.0,
    "legal_margin_x": 61.0,
    "qr_from_right": 64.0,
    "qr_from_bottom": 40.0,
    "qr_max_side": 120.0,
}

_MESES_ES = (
    "ENERO",
    "FEBRERO",
    "MARZO",
    "ABRIL",
    "MAYO",
    "JUNIO",
    "JULIO",
    "AGOSTO",
    "SEPTIEMBRE",
    "OCTUBRE",
    "NOVIEMBRE",
    "DICIEMBRE",
)

_CERT_KIND_ES = {
    "basic": "Básico",
    "advanced": "Avanzado",
    "diploma": "Diplomado",
}


def _identity_phrase(identity_type: str, identity_number: str) -> str:
    t = (identity_type or "").upper().strip()
    if t == "CC":
        kind = "CÉDULA DE CIUDADANÍA"
    elif t == "TI":
        kind = "TARJETA DE IDENTIDAD"
    else:
        kind = "DOCUMENTO DE IDENTIDAD"
    return f"IDENTIFICADO CON {kind} No. {identity_number}"


def _legal_paragraph_text(issued_on: date) -> str:
    day = issued_on.day
    month = _MESES_ES[issued_on.month - 1]
    year = issued_on.year
    return (
        f"ESTE CERTIFICADO ES EXPEDIDO EN LA CIUDAD DE BOGOTÁ A LOS {day} DÍAS "
        f"DEL MES DE {month} DEL {year}, LA PRESENTE CERTIFICACIÓN SE EXPIDE MEDIANTE "
        "EL MARCO NORMATIVO PARA LA EDUCACIÓN INFORMAL Y NO CONDUCE A TITULO ALGUNO O "
        "CERTIFICACIÓN DE APTITUD OCUPACIONAL."
    )


def _font_candidates() -> dict[str, list[str]]:
    return {
        "TrebuchetMS": [
            "/usr/share/fonts/truetype/msttcorefonts/Trebuchet_MS.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/trebuc.ttf",
            "C:/Windows/fonts/trebuc.ttf",
            "C:/Windows/fonts/trebucbd.ttf",
        ],
        "Tahoma": [
            "/usr/share/fonts/truetype/msttcorefonts/Tahoma.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/tahoma.ttf",
            "C:/Windows/fonts/tahoma.ttf",
        ],
        "Cambria": [
            "/usr/share/fonts/truetype/msttcorefonts/cambria.ttc",
            "/usr/share/fonts/truetype/msttcorefonts/Cambria.ttf",
            "C:/Windows/fonts/cambria.ttc",
            "C:/Windows/fonts/cambria.ttf",
        ],
    }


def _register_fonts() -> dict[str, str]:
    """Registra TTFonts y devuelve nombre ReportLab por familia lógica."""
    out: dict[str, str] = {}
    for logical, paths in _font_candidates().items():
        for p in paths:
            path = Path(p)
            if not path.is_file():
                continue
            try:
                if path.suffix.lower() == ".ttc":
                    try:
                        pdfmetrics.registerFont(
                            TTFont(logical, str(path), subfontIndex=0)
                        )
                    except Exception:
                        continue
                else:
                    pdfmetrics.registerFont(TTFont(logical, str(path)))
                out[logical] = logical
                break
            except Exception:
                continue
    # Fallbacks
    if "TrebuchetMS" not in out:
        for p in (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ):
            if Path(p).is_file():
                pdfmetrics.registerFont(TTFont("TrebuchetMS", p))
                out["TrebuchetMS"] = "TrebuchetMS"
                break
    if "Tahoma" not in out:
        for p in (
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ):
            if Path(p).is_file():
                pdfmetrics.registerFont(TTFont("Tahoma", p))
                out["Tahoma"] = "Tahoma"
                break
    if "Cambria" not in out:
        for p in (
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        ):
            if Path(p).is_file():
                pdfmetrics.registerFont(TTFont("Cambria", p))
                out["Cambria"] = "Cambria"
                break
    return out


_registered: dict[str, str] | None = None


def _fonts() -> dict[str, str]:
    global _registered
    if _registered is None:
        _registered = _register_fonts()
    return _registered


@dataclass(frozen=True)
class CertificateEditorData:
    issued_on: date
    student_full_name: str
    identity_type: str
    identity_number: str
    certificate_type_kind: str
    certificate_type_name: str
    hours: int


class CertificateEditor:
    """
    Fusiona ``certificate_template.pdf`` con una capa de texto + QR.
    ``certificate_reference.pdf`` sirve solo como guía visual para ajustar ``_LAYOUT``.
    """

    def __init__(self, base_pdf_path: Path | str | None = None) -> None:
        default = (
            Path(__file__).resolve().parent.parent
            / "templates"
            / "certificate_template.pdf"
        )
        self._base_pdf_path = (
            Path(base_pdf_path) if base_pdf_path is not None else default
        )

    @property
    def base_pdf_path(self) -> Path:
        return self._base_pdf_path

    def build_merged_pdf(
        self, data: CertificateEditorData, qr_png: BinaryIO
    ) -> BytesIO:
        if not self._base_pdf_path.is_file():
            msg = f"No existe la plantilla PDF: {self._base_pdf_path}"
            raise FileNotFoundError(msg)

        base_reader = PdfReader(str(self._base_pdf_path))
        if not base_reader.pages:
            msg = "La plantilla no tiene páginas"
            raise ValueError(msg)

        page0 = base_reader.pages[0]
        mb = page0.mediabox
        w_pt = float(mb.width)
        h_pt = float(mb.height)

        overlay_buf = self._build_overlay_pdf(data, qr_png, w_pt, h_pt)
        overlay_reader = PdfReader(overlay_buf)

        writer = PdfWriter()
        merged = page0
        merged.merge_page(overlay_reader.pages[0])
        writer.add_page(merged)
        for i in range(1, len(base_reader.pages)):
            writer.add_page(base_reader.pages[i])

        out = BytesIO()
        writer.write(out)
        out.seek(0)
        return out

    def _build_overlay_pdf(
        self,
        data: CertificateEditorData,
        qr_png: BinaryIO,
        w_pt: float,
        h_pt: float,
    ) -> BytesIO:
        fonts = _fonts()
        f_treb = fonts.get("TrebuchetMS", "Helvetica")
        f_tahoma = fonts.get("Tahoma", "Helvetica")
        f_cambria = fonts.get("Cambria", "Helvetica")

        buf = BytesIO()
        c = rl_canvas.Canvas(buf, pagesize=(w_pt, h_pt))
        cx = w_pt / 2.0
        blue = HexColor("#004A98")
        navy = HexColor("#051C49")

        kind_es = _CERT_KIND_ES.get(
            (data.certificate_type_kind or "").lower(),
            data.certificate_type_kind or "",
        )
        course_line = f"Asistió al Curso {kind_es}"

        # Nombre estudiante
        c.setFont(f_treb, 32.5)
        c.setFillColor(blue)
        c.drawCentredString(
            cx, _LAYOUT["student_name_y"], (data.student_full_name).upper()
        )

        # Identidad
        c.setFont(f_tahoma, 17)
        c.setFillColor(navy)
        c.drawCentredString(
            cx,
            _LAYOUT["identity_y"],
            _identity_phrase(data.identity_type, data.identity_number),
        )

        # Curso / tipo
        c.setFont(f_cambria, 18)
        c.setFillColor(navy)
        c.drawCentredString(cx, _LAYOUT["course_line_y"], course_line)

        # Nombre certificado
        c.setFont(f_tahoma, 17)
        c.drawCentredString(
            cx, _LAYOUT["cert_name_y"], (data.certificate_type_name).upper()
        )

        # Horas
        c.setFont(f_cambria, 18)
        c.drawCentredString(
            cx,
            _LAYOUT["hours_y"],
            f"Con una intensidad horaria de {data.hours} horas",
        )

        # Párrafo legal
        legal = html.escape(_legal_paragraph_text(data.issued_on))
        style = ParagraphStyle(
            name="legal",
            fontName=f_tahoma,
            fontSize=9,
            leading=11,
            textColor=navy,
            alignment=TA_CENTER,
        )
        para = Paragraph(legal.replace("\n", "<br/>"), style)
        aw = _LAYOUT["legal_max_width"]
        ah = 400.0
        tw, th = para.wrap(aw, ah)
        x_para = (w_pt - tw) / 2.0
        y_para = _LAYOUT["legal_top_y"] - th
        para.drawOn(c, x_para, y_para)

        # QR
        qr_png.seek(0)
        ir = ImageReader(qr_png)
        side = min(_LAYOUT["qr_max_side"], h_pt * 0.22, w_pt * 0.18)
        qx = w_pt - _LAYOUT["qr_from_right"] - side
        qy = _LAYOUT["qr_from_bottom"]
        c.drawImage(ir, qx, qy, width=side, height=side, mask="auto")

        c.showPage()
        c.save()
        buf.seek(0)
        return buf


def apply_revoked_watermark_pdf(
    pdf_bytes: bytes,
    *,
    watermark_text: str = "REVOCADO",
) -> bytes:
    """Superpone una marca de agua diagonal muy visible sobre cada página."""
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    font = "Helvetica-Bold"
    for page in reader.pages:
        mb = page.mediabox
        w_pt = float(mb.width)
        h_pt = float(mb.height)
        overlay = BytesIO()
        c = rl_canvas.Canvas(overlay, pagesize=(w_pt, h_pt))
        c.saveState()
        c.setFillColorRGB(0.75, 0.05, 0.05)
        try:
            c.setFillAlpha(0.55)
        except Exception:
            pass
        fs = min(w_pt, h_pt) * 0.11
        c.setFont(font, fs)
        c.translate(w_pt / 2.0, h_pt / 2.0)
        c.rotate(45)
        # c.rotate(32)
        # c.drawCentredString(0, 0, watermark_text)
        # c.rotate(-18)
        # c.setFont(font, fs * 0.65)
        c.drawCentredString(0, -fs * 1.2, watermark_text)
        c.restoreState()
        c.save()
        overlay.seek(0)
        stamp = PdfReader(overlay).pages[0]
        page.merge_page(stamp)
        writer.add_page(page)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()
