"""Fixtures for Cat Care Tracker tests."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import date

from homeassistant.core import HomeAssistant


@pytest.fixture
def mock_google_sheets_client():
    """Create a mock Google Sheets OAuth client."""
    with patch(
        "custom_components.cat_care_tracker.google_sheets.GoogleSheetsOAuthClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.test_connection.return_value = True
        mock_client.append_entry.return_value = True
        mock_client.get_entries.return_value = [
            {
                "Timestamp": "01/15/2024 08:30:00",
                "Date": "01/15/2024 08:30",
                "Checkin Type": "Food, Insulin",
                "Water Refill": "",
                "BG (mg/dL)": "",
            },
            {
                "Timestamp": "01/15/2024 07:00:00",
                "Date": "01/15/2024 07:00",
                "Checkin Type": "Water",
                "Water Refill": "250ml",
                "BG (mg/dL)": "",
            },
        ]
        mock_client.get_entries_for_date.return_value = [
            {
                "Timestamp": "01/15/2024 08:30:00",
                "Date": "01/15/2024 08:30",
                "Checkin Type": "Food, Insulin",
                "Water Refill": "",
                "BG (mg/dL)": "",
            },
        ]
        mock_client.get_last_entry_by_type.return_value = {
            "Timestamp": "01/15/2024 08:30:00",
            "Date": "01/15/2024 08:30",
            "Checkin Type": "Food",
            "Water Refill": "",
            "BG (mg/dL)": "",
        }
        mock_client.get_today_counts.return_value = {
            "Food": 2,
            "Water": 1,
            "Insulin": 2,
            "Blood Glucose Measurement": 0,
        }
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    mock_entry = MagicMock()
    mock_entry.entry_id = "test_entry_id"
    mock_entry.data = {
        "spreadsheet_id": "test_spreadsheet_id",
        "cat_name": "Whiskers",
        "token": {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_at": 9999999999,
        },
    }
    return mock_entry
