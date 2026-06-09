"""Plantillas HTML para correos electrónicos."""


def credentials_body(app_name: str, email_to: str, password: str, login_url: str) -> str:
    return f"""<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2>Bienvenido a {app_name}</h2>
    <p>Tu cuenta ha sido creada exitosamente. Estas son tus credenciales de acceso:</p>
    <p><strong>Correo:</strong> {email_to}</p>
    <p><strong>Contraseña:</strong> {password}</p>
    <p>Puedes acceder en el siguiente enlace:</p>
    <p><a href="{login_url}">{login_url}</a></p>
</body>
</html>"""


def issued_body(app_name: str, student_name: str, verify_link: str) -> str:
    return f"""<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2>Certificado Emitido</h2>
    <p>Hola <strong>{student_name}</strong>,</p>
    <p>Te informamos que tu certificado ha sido emitido exitosamente.</p>
    <p>Puedes verificar y descargar tu certificado en el siguiente enlace:</p>
    <p><a href="{verify_link}">{verify_link}</a></p>
    <p>Si tienes alguna duda, por favor contacta al administrador.</p>
</body>
</html>"""


def expired_body(app_name: str, student_name: str) -> str:
    return f"""<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2>Certificado Expirado</h2>
    <p>Hola <strong>{student_name}</strong>,</p>
    <p>Te informamos que tu certificado ha expirado.</p>
    <p>Si deseas obtener un nuevo certificado, por favor contacta al administrador.</p>
</body>
</html>"""
