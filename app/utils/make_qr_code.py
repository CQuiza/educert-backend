"""Generación de códigos QR en memoria (BytesIO)."""

from __future__ import annotations

from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_M


class MakeQRCode:
    """Construye un QR PNG en ``BytesIO`` a partir de una URL o texto (p. ej. UUID)."""

    def __init__(
        self,
        *,
        box_size: int = 10,
        border: int = 2,
        error_correction: int = ERROR_CORRECT_M,
    ) -> None:
        self._box_size = box_size
        self._border = border
        self._error_correction = error_correction

    def to_bytesio(self, url_or_uuid: str) -> BytesIO:
        """
        Codifica ``url_or_uuid`` tal cual en el QR (URL completa, UUID como texto, etc.).
        El caller suele pasar la URL pública de verificación.
        """
        qr = qrcode.QRCode(
            version=None,
            error_correction=self._error_correction,
            box_size=self._box_size,
            border=self._border,
        )
        qr.add_data(url_or_uuid)
        qr.make(fit=True)
        img = qr.make_image()
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
