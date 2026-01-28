"""Google Sheets API handler for Cat Care Tracker."""
from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .const import (
    COL_TIMESTAMP,
    COL_DATE,
    COL_CHECKIN_TYPE,
    COL_WATER_REFILL,
    COL_BG_LEVEL,
    CHECKIN_TYPE_FOOD,
    CHECKIN_TYPE_INSULIN,
    CHECKIN_TYPE_WATER,
    CHECKIN_TYPE_BG,
)

_LOGGER = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class GoogleSheetsClient:
    """Client for interacting with Google Sheets."""

    def __init__(self, credentials_file: str, spreadsheet_id: str) -> None:
        """Initialize the Google Sheets client."""
        self._credentials_file = credentials_file
        self._spreadsheet_id = spreadsheet_id
        self._service = None
        self._sheet_name = "Sheet1"  # Default sheet name

    async def async_connect(self) -> bool:
        """Connect to Google Sheets API."""
        try:
            creds = Credentials.from_service_account_file(
                self._credentials_file, scopes=SCOPES
            )
            self._service = build("sheets", "v4", credentials=creds)
            # Test connection by reading the spreadsheet
            self._service.spreadsheets().get(
                spreadsheetId=self._spreadsheet_id
            ).execute()
            return True
        except FileNotFoundError:
            _LOGGER.error("Credentials file not found: %s", self._credentials_file)
            return False
        except HttpError as err:
            _LOGGER.error("Failed to connect to Google Sheets: %s", err)
            return False
        except Exception as err:
            _LOGGER.error("Unexpected error connecting to Google Sheets: %s", err)
            return False

    def connect(self) -> bool:
        """Connect to Google Sheets API (synchronous)."""
        try:
            creds = Credentials.from_service_account_file(
                self._credentials_file, scopes=SCOPES
            )
            self._service = build("sheets", "v4", credentials=creds)
            # Test connection by reading the spreadsheet
            self._service.spreadsheets().get(
                spreadsheetId=self._spreadsheet_id
            ).execute()
            return True
        except FileNotFoundError:
            _LOGGER.error("Credentials file not found: %s", self._credentials_file)
            return False
        except HttpError as err:
            _LOGGER.error("Failed to connect to Google Sheets: %s", err)
            return False
        except Exception as err:
            _LOGGER.error("Unexpected error connecting to Google Sheets: %s", err)
            return False

    def append_entry(
        self,
        checkin_types: list[str],
        water_refill: str | None = None,
        bg_level: int | None = None,
        entry_date: date | None = None,
        entry_time: str | None = None,
    ) -> bool:
        """Append a new entry to the Google Sheet.

        Args:
            checkin_types: List of check-in types (Food, Water, Insulin, Blood Glucose Measurement)
            water_refill: Amount of water refill (optional)
            bg_level: Blood glucose level in mg/dL (optional)
            entry_date: Date of the entry (defaults to today)
            entry_time: Time of the entry (defaults to current time)

        Returns:
            True if successful, False otherwise
        """
        if not self._service:
            _LOGGER.error("Not connected to Google Sheets")
            return False

        try:
            now = datetime.now()
            timestamp = now.strftime("%m/%d/%Y %H:%M:%S")

            if entry_date is None:
                entry_date = now.date()

            if entry_time:
                date_str = f"{entry_date.strftime('%m/%d/%Y')} {entry_time}"
            else:
                date_str = entry_date.strftime("%m/%d/%Y")

            # Format checkin types as comma-separated string
            checkin_type_str = ", ".join(checkin_types)

            # Prepare the row data matching the columns:
            # Timestamp, Date, Checkin Type, Water Refill, BG (mg/dL)
            row = [
                timestamp,
                date_str,
                checkin_type_str,
                water_refill if water_refill else "",
                str(bg_level) if bg_level else "",
            ]

            body = {"values": [row]}

            self._service.spreadsheets().values().append(
                spreadsheetId=self._spreadsheet_id,
                range=f"{self._sheet_name}!A:E",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=body,
            ).execute()

            _LOGGER.info("Successfully appended entry: %s", row)
            return True

        except HttpError as err:
            _LOGGER.error("Failed to append entry: %s", err)
            return False
        except Exception as err:
            _LOGGER.error("Unexpected error appending entry: %s", err)
            return False

    def get_entries(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get recent entries from the Google Sheet.

        Args:
            limit: Maximum number of entries to retrieve

        Returns:
            List of entry dictionaries
        """
        if not self._service:
            _LOGGER.error("Not connected to Google Sheets")
            return []

        try:
            result = (
                self._service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=self._spreadsheet_id,
                    range=f"{self._sheet_name}!A:E",
                )
                .execute()
            )

            values = result.get("values", [])

            if not values:
                return []

            # First row is header
            headers = values[0] if values else []
            entries = []

            # Process rows in reverse order (newest first), skip header
            for row in reversed(values[1:limit + 1]):
                entry = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        entry[header] = row[i]
                    else:
                        entry[header] = ""
                entries.append(entry)

            return entries

        except HttpError as err:
            _LOGGER.error("Failed to get entries: %s", err)
            return []
        except Exception as err:
            _LOGGER.error("Unexpected error getting entries: %s", err)
            return []

    def get_entries_for_date(self, target_date: date) -> list[dict[str, Any]]:
        """Get entries for a specific date.

        Args:
            target_date: The date to filter entries

        Returns:
            List of entry dictionaries for the specified date
        """
        all_entries = self.get_entries(limit=500)
        date_str = target_date.strftime("%m/%d/%Y")

        entries = []
        for entry in all_entries:
            entry_date = entry.get(COL_DATE, "")
            # Handle date with time format
            if entry_date.startswith(date_str):
                entries.append(entry)

        return entries

    def get_last_entry_by_type(self, checkin_type: str) -> dict[str, Any] | None:
        """Get the most recent entry of a specific check-in type.

        Args:
            checkin_type: The check-in type to filter

        Returns:
            The most recent entry of the specified type, or None
        """
        entries = self.get_entries(limit=500)

        for entry in entries:
            types = entry.get(COL_CHECKIN_TYPE, "")
            if checkin_type in types:
                return entry

        return None

    def get_today_counts(self) -> dict[str, int]:
        """Get counts of each check-in type for today.

        Returns:
            Dictionary with counts for each check-in type
        """
        today_entries = self.get_entries_for_date(date.today())

        counts = {
            CHECKIN_TYPE_FOOD: 0,
            CHECKIN_TYPE_WATER: 0,
            CHECKIN_TYPE_INSULIN: 0,
            CHECKIN_TYPE_BG: 0,
        }

        for entry in today_entries:
            types = entry.get(COL_CHECKIN_TYPE, "")
            for checkin_type in counts:
                if checkin_type in types:
                    counts[checkin_type] += 1

        return counts
