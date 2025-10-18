# Formulario-App

Aplicación de formulario construida con [Streamlit](https://streamlit.io/) para registrar información en un archivo de Excel almacenado en Google Drive. El formulario permite ingresar datos de contacto y comentarios de los usuarios, los cuales se anexan automáticamente al Excel.

## Requisitos

- Python 3.10 o superior.
- Credenciales de una cuenta de servicio de Google con acceso a Google Drive.
- Un archivo de Excel ya creado en Google Drive que recibirá los registros.

## Configuración de Google Drive

1. Crea un **proyecto** en Google Cloud Console y habilita la **Google Drive API**.
2. Genera una **cuenta de servicio** y descarga el archivo JSON con las credenciales.
3. Sube el archivo de Excel a Google Drive y comparte el archivo con el correo de la cuenta de servicio otorgándole permisos de editor.
4. Localiza el ID del archivo de Excel (se encuentra en la URL cuando abres el archivo en Drive).

## Instalación del proyecto

Clona el repositorio y prepara un entorno virtual:

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows usa .venv\Scripts\activate
pip install -r requirements.txt
```

Guarda las credenciales del servicio de Google en un archivo (por ejemplo `service-account.json`) y define las siguientes variables de entorno antes de ejecutar la aplicación:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/ruta/al/service-account.json"
export DRIVE_FILE_ID="<ID_DEL_ARCHIVO>"
export DRIVE_SHEET_NAME="Respuestas"  # Opcional, nombre de la hoja dentro del Excel
```

También puedes definir estos valores en el archivo `~/.streamlit/secrets.toml`:

```toml
[drive]
file_id = "<ID_DEL_ARCHIVO>"
sheet_name = "Respuestas"
credentials_path = "/ruta/al/service-account.json"
```

## Ejecución

Inicia la aplicación con Streamlit:

```bash
streamlit run app.py
```

Desde el navegador se abrirá el formulario donde podrás ingresar los datos. Al enviar el formulario los registros se anexarán al archivo de Excel y podrás ver los últimos valores ingresados directamente en la interfaz.
