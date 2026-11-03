from planeta.comandos import crear_bot
from planeta.configuracion import leer_id_servidor, leer_token
from planeta.cuestionario import validar_contenido
from planeta.errores import ErrorDeConfiguracion
from planeta.servicios import crear_servicios

MENSAJE_SIN_TOKEN = (
    "Falta el token. Crea un archivo llamado token.txt en la misma carpeta que bot.py "
    "y pega adentro SOLO el token del bot (nada más)."
)


def principal() -> None:
    try:
        validar_contenido()
        token = leer_token()
        if token is None:
            raise ErrorDeConfiguracion(MENSAJE_SIN_TOKEN)
        bot = crear_bot(crear_servicios(), leer_id_servidor())
    except ErrorDeConfiguracion as error:
        raise SystemExit(str(error)) from error
    bot.run(token)


if __name__ == "__main__":
    principal()
