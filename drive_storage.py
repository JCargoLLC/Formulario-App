from __future__ import annotations

import io
import os
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload


SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.readonly",
]


class DriveStorageError(RuntimeError):
    """Custom error raised when Google Drive operations fail."""


@dataclass
class DriveExcelStorage:
    """Utility class to keep a Google Drive hosted Excel file in sync.

    Parameters
    ----------
    credentials_path:
        Path to the JSON file with the service account credentials. If not
        provided the path will be read from the ``GOOGLE_APPLICATION_CREDENTIALS``
        environment variable.
    file_id:
        Identifier of the Excel file stored on Google Drive.
    sheet_name:
        Name of the sheet inside the Excel workbook where the data is stored.
    columns:
        List of column names expected in the Excel workbook. When the workbook is
        created for the first time these names will be used to build the header.
    """

    file_id: str
    sheet_name: str
    columns: List[str]
    credentials_path: str | None = None

    def __post_init__(self) -> None:
        path = self.credentials_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not path:
            raise DriveStorageError(
                "No se encontró la ruta al archivo de credenciales. "
                "Define GOOGLE_APPLICATION_CREDENTIALS o proporciona credentials_path."
            )

        try:
            credentials = service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
        except (OSError, ValueError) as exc:
            raise DriveStorageError(f"No se pudieron cargar las credenciales: {exc}") from exc

        self._service = build("drive", "v3", credentials=credentials)

    def _download_excel_bytes(self) -> io.BytesIO | None:
        request = self._service.files().get_media(fileId=self.file_id)
        file_handle = io.BytesIO()
        downloader = MediaIoBaseDownload(file_handle, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                # Just iterate until download completes; progress is not shown in UI
                pass

        file_handle.seek(0)
        return file_handle

    def _upload_excel_bytes(self, content: io.BytesIO) -> None:
        media_body = MediaIoBaseUpload(content, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", resumable=True)
        content.seek(0)
        update_request = self._service.files().update(fileId=self.file_id, media_body=media_body)
        update_request.execute()

    def _load_existing_records(self) -> pd.DataFrame:
        try:
            excel_bytes = self._download_excel_bytes()
        except HttpError as exc:
            if exc.resp.status == 404:
                return pd.DataFrame(columns=self.columns)
            raise DriveStorageError(f"No se pudo descargar el archivo de Excel: {exc}") from exc

        try:
            return pd.read_excel(excel_bytes, sheet_name=self.sheet_name)
        except ValueError:
            # If the sheet does not exist yet we create it with the desired header
            return pd.DataFrame(columns=self.columns)

    def append_record(self, record: Dict[str, str]) -> pd.DataFrame:
        """Append a record to the Excel file and return the updated dataframe."""
        df = self._load_existing_records()
        new_row = {column: record.get(column, "") for column in self.columns}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=self.sheet_name, index=False)
        output.seek(0)

        try:
            self._upload_excel_bytes(output)
        except HttpError as exc:
            raise DriveStorageError(f"No se pudo subir el archivo actualizado: {exc}") from exc

        return df

    def get_records(self) -> pd.DataFrame:
        """Return the current contents of the Excel sheet."""
        return self._load_existing_records()


__all__ = ["DriveExcelStorage", "DriveStorageError"]
