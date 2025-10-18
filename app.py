"""Aplicación Streamlit para registrar datos en un Excel alojado en Google Drive."""
from __future__ import annotations

import os
from typing import Any, Dict

import streamlit as st

from drive_storage import DriveExcelStorage, DriveStorageError

DEFAULT_COLUMNS = ["Nombre", "Correo", "Teléfono", "Comentarios"]
DEFAULT_SHEET_NAME = "Respuestas"


def _resolve_configuration() -> Dict[str, str | None]:
    secrets_drive = st.secrets.get("drive", {}) if hasattr(st, "secrets") else {}
    return {
        "file_id": secrets_drive.get("file_id") or os.environ.get("DRIVE_FILE_ID"),
        "credentials_path": secrets_drive.get("credentials_path") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
        "sheet_name": secrets_drive.get("sheet_name") or os.environ.get("DRIVE_SHEET_NAME") or DEFAULT_SHEET_NAME,
    }


@st.cache_resource(show_spinner=False)
def get_storage() -> DriveExcelStorage:
    config = _resolve_configuration()
    if not config["file_id"]:
        raise DriveStorageError(
            "Debes configurar el identificador del archivo de Excel. "
            "Utiliza st.secrets['drive']['file_id'] o la variable de entorno DRIVE_FILE_ID."
        )

    storage = DriveExcelStorage(
        file_id=config["file_id"],
        sheet_name=config["sheet_name"],
        columns=DEFAULT_COLUMNS,
        credentials_path=config["credentials_path"],
    )
    return storage


def _build_form() -> Dict[str, Any]:
    with st.form("registro_formulario"):
        nombre = st.text_input("Nombre completo", max_chars=100)
        correo = st.text_input("Correo electrónico", max_chars=120)
        telefono = st.text_input("Teléfono de contacto", max_chars=50)
        comentarios = st.text_area("Comentarios o necesidades", max_chars=500)
        enviado = st.form_submit_button("Enviar")

    return {
        "submitted": enviado,
        "data": {
            "Nombre": nombre.strip(),
            "Correo": correo.strip(),
            "Teléfono": telefono.strip(),
            "Comentarios": comentarios.strip(),
        },
    }


def main() -> None:
    st.set_page_config(page_title="Formulario App", page_icon="📝", layout="centered")
    st.title("Registro de interesados")
    st.write(
        "Completa el formulario para registrar un nuevo interesado. "
        "Los datos se guardarán automáticamente en el archivo de Excel alojado en Google Drive."
    )

    try:
        storage = get_storage()
    except DriveStorageError as exc:
        st.error(str(exc))
        st.stop()

    result = _build_form()
    if result["submitted"]:
        record = result["data"]
        if not record["Nombre"] or not record["Correo"]:
            st.warning("El nombre y el correo electrónico son obligatorios.")
        else:
            try:
                df = storage.append_record(record)
            except DriveStorageError as exc:
                st.error(f"Ocurrió un error al guardar la información: {exc}")
            else:
                st.success("¡Registro guardado correctamente!")
                st.dataframe(df.tail(10), use_container_width=True)

    with st.expander("Ver registros guardados"):
        if st.button("Actualizar registros"):
            try:
                df = storage.get_records()
            except DriveStorageError as exc:
                st.error(f"No se pudieron recuperar los registros: {exc}")
            else:
                if df.empty:
                    st.info("Aún no hay registros guardados.")
                else:
                    st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
