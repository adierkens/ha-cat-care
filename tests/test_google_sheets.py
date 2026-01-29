"""Tests for Cat Care Tracker Google Sheets client."""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from custom_components.cat_care_tracker.google_sheets import (
    GoogleSheetsOAuthClient,
    GoogleSheetsClient,
)
from custom_components.cat_care_tracker.const import (
    CHECKIN_TYPE_FOOD,
    CHECKIN_TYPE_INSULIN,
    CHECKIN_TYPE_WATER,
    CHECKIN_TYPE_BG,
)


class TestGoogleSheetsOAuthClient:
    """Tests for GoogleSheetsOAuthClient."""

    def test_init(self):
        """Test client initialization."""
        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id")
        assert client._access_token == "test_token"
        assert client._spreadsheet_id == "test_spreadsheet_id"
        assert client._service is None
        assert client._sheet_name == "Sheet1"

    def test_init_custom_sheet_name(self):
        """Test client initialization with custom sheet name."""
        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id", "CustomSheet")
        assert client._access_token == "test_token"
        assert client._spreadsheet_id == "test_spreadsheet_id"
        assert client._service is None
        assert client._sheet_name == "CustomSheet"

    @patch("custom_components.cat_care_tracker.google_sheets.build")
    @patch("custom_components.cat_care_tracker.google_sheets.OAuthCredentials")
    def test_test_connection_success(self, mock_creds, mock_build):
        """Test successful connection."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id")
        success, error_code = client.test_connection()

        assert success is True
        assert error_code is None
        mock_creds.assert_called_once_with(token="test_token")

    @patch("custom_components.cat_care_tracker.google_sheets.build")
    @patch("custom_components.cat_care_tracker.google_sheets.OAuthCredentials")
    def test_test_connection_failure(self, mock_creds, mock_build):
        """Test connection failure."""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_service.spreadsheets().get().execute.side_effect = HttpError(
            resp=MagicMock(status=404), content=b"Not found"
        )
        mock_build.return_value = mock_service

        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id")
        success, error_code = client.test_connection()

        assert success is False
        assert error_code == "not_found"

    @patch("custom_components.cat_care_tracker.google_sheets.build")
    @patch("custom_components.cat_care_tracker.google_sheets.OAuthCredentials")
    def test_test_connection_permission_denied(self, mock_creds, mock_build):
        """Test connection failure due to permission denied."""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_service.spreadsheets().get().execute.side_effect = HttpError(
            resp=MagicMock(status=403), content=b"Permission denied"
        )
        mock_build.return_value = mock_service

        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id")
        success, error_code = client.test_connection()

        assert success is False
        assert error_code == "permission_denied"

    @patch("custom_components.cat_care_tracker.google_sheets.build")
    @patch("custom_components.cat_care_tracker.google_sheets.OAuthCredentials")
    def test_test_connection_invalid_credentials(self, mock_creds, mock_build):
        """Test connection failure due to invalid credentials."""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_service.spreadsheets().get().execute.side_effect = HttpError(
            resp=MagicMock(status=401), content=b"Invalid credentials"
        )
        mock_build.return_value = mock_service

        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id")
        success, error_code = client.test_connection()

        assert success is False
        assert error_code == "invalid_credentials"

    @patch("custom_components.cat_care_tracker.google_sheets.build")
    @patch("custom_components.cat_care_tracker.google_sheets.OAuthCredentials")
    def test_append_entry(self, mock_creds, mock_build):
        """Test appending an entry."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id")
        result = client.append_entry([CHECKIN_TYPE_FOOD, CHECKIN_TYPE_INSULIN])

        assert result is True
        mock_service.spreadsheets().values().append.assert_called_once()

    @patch("custom_components.cat_care_tracker.google_sheets.build")
    @patch("custom_components.cat_care_tracker.google_sheets.OAuthCredentials")
    def test_append_entry_with_water(self, mock_creds, mock_build):
        """Test appending a water entry."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id")
        result = client.append_entry([CHECKIN_TYPE_WATER], water_refill="250ml")

        assert result is True

    @patch("custom_components.cat_care_tracker.google_sheets.build")
    @patch("custom_components.cat_care_tracker.google_sheets.OAuthCredentials")
    def test_append_entry_with_bg(self, mock_creds, mock_build):
        """Test appending a blood glucose entry."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id")
        result = client.append_entry([CHECKIN_TYPE_BG], bg_level=120)

        assert result is True

    @patch("custom_components.cat_care_tracker.google_sheets.build")
    @patch("custom_components.cat_care_tracker.google_sheets.OAuthCredentials")
    def test_append_entry_custom_sheet_name(self, mock_creds, mock_build):
        """Test appending an entry with custom sheet name."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id", "MySheet")
        result = client.append_entry([CHECKIN_TYPE_FOOD])

        assert result is True
        # Verify the call was made with the custom sheet name
        call_args = mock_service.spreadsheets().values().append.call_args
        assert call_args[1]["range"] == "MySheet!A:E"

    @patch("custom_components.cat_care_tracker.google_sheets.build")
    @patch("custom_components.cat_care_tracker.google_sheets.OAuthCredentials")
    def test_get_entries(self, mock_creds, mock_build):
        """Test getting entries."""
        mock_service = MagicMock()
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["Timestamp", "Date", "Checkin Type", "Water Refill", "BG (mg/dL)"],
                ["01/15/2024 08:30:00", "01/15/2024 08:30", "Food", "", ""],
                ["01/15/2024 07:00:00", "01/15/2024 07:00", "Water", "250ml", ""],
            ]
        }
        mock_build.return_value = mock_service

        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id")
        entries = client.get_entries(limit=10)

        assert len(entries) == 2
        # Entries should be in reverse chronological order
        assert entries[0]["Checkin Type"] == "Water"
        assert entries[1]["Checkin Type"] == "Food"

    @patch("custom_components.cat_care_tracker.google_sheets.build")
    @patch("custom_components.cat_care_tracker.google_sheets.OAuthCredentials")
    def test_get_entries_empty(self, mock_creds, mock_build):
        """Test getting entries when empty."""
        mock_service = MagicMock()
        mock_service.spreadsheets().values().get().execute.return_value = {"values": []}
        mock_build.return_value = mock_service

        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id")
        entries = client.get_entries()

        assert entries == []

    @patch("custom_components.cat_care_tracker.google_sheets.build")
    @patch("custom_components.cat_care_tracker.google_sheets.OAuthCredentials")
    def test_get_today_counts(self, mock_creds, mock_build):
        """Test getting today's counts."""
        today_str = date.today().strftime("%m/%d/%Y")
        mock_service = MagicMock()
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["Timestamp", "Date", "Checkin Type", "Water Refill", "BG (mg/dL)"],
                [f"{today_str} 08:30:00", f"{today_str} 08:30", "Food, Insulin", "", ""],
                [f"{today_str} 12:00:00", f"{today_str} 12:00", "Food", "", ""],
                [f"{today_str} 07:00:00", f"{today_str} 07:00", "Water", "250ml", ""],
            ]
        }
        mock_build.return_value = mock_service

        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id")
        counts = client.get_today_counts()

        assert counts[CHECKIN_TYPE_FOOD] == 2
        assert counts[CHECKIN_TYPE_INSULIN] == 1
        assert counts[CHECKIN_TYPE_WATER] == 1
        assert counts[CHECKIN_TYPE_BG] == 0

    @patch("custom_components.cat_care_tracker.google_sheets.build")
    @patch("custom_components.cat_care_tracker.google_sheets.OAuthCredentials")
    def test_get_last_entry_by_type(self, mock_creds, mock_build):
        """Test getting the last entry of a specific type."""
        mock_service = MagicMock()
        mock_service.spreadsheets().values().get().execute.return_value = {
            "values": [
                ["Timestamp", "Date", "Checkin Type", "Water Refill", "BG (mg/dL)"],
                ["01/15/2024 12:00:00", "01/15/2024 12:00", "Water", "300ml", ""],
                ["01/15/2024 08:30:00", "01/15/2024 08:30", "Food, Insulin", "", ""],
                ["01/15/2024 07:00:00", "01/15/2024 07:00", "Food", "", ""],
            ]
        }
        mock_build.return_value = mock_service

        client = GoogleSheetsOAuthClient("test_token", "test_spreadsheet_id")

        # Most recent Water entry
        water_entry = client.get_last_entry_by_type(CHECKIN_TYPE_WATER)
        assert water_entry is not None
        assert water_entry["Water Refill"] == "300ml"

        # Most recent Food entry (should be the one with Insulin)
        food_entry = client.get_last_entry_by_type(CHECKIN_TYPE_FOOD)
        assert food_entry is not None
        assert "Insulin" in food_entry["Checkin Type"]


class TestGoogleSheetsClient:
    """Tests for the service account based GoogleSheetsClient."""

    def test_init(self):
        """Test client initialization."""
        client = GoogleSheetsClient("/path/to/creds.json", "test_spreadsheet_id")
        assert client._credentials_file == "/path/to/creds.json"
        assert client._spreadsheet_id == "test_spreadsheet_id"
        assert client._service is None
        assert client._sheet_name == "Sheet1"

    def test_init_custom_sheet_name(self):
        """Test client initialization with custom sheet name."""
        client = GoogleSheetsClient("/path/to/creds.json", "test_spreadsheet_id", "CustomSheet")
        assert client._credentials_file == "/path/to/creds.json"
        assert client._spreadsheet_id == "test_spreadsheet_id"
        assert client._service is None
        assert client._sheet_name == "CustomSheet"

    def test_connect_file_not_found(self):
        """Test connection with missing credentials file."""
        client = GoogleSheetsClient("/nonexistent/path.json", "test_spreadsheet_id")
        result = client.connect()
        assert result is False

    @patch("custom_components.cat_care_tracker.google_sheets.build")
    @patch("custom_components.cat_care_tracker.google_sheets.ServiceAccountCredentials")
    def test_connect_success(self, mock_creds, mock_build):
        """Test successful connection."""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        with patch("builtins.open", MagicMock()):
            mock_creds.from_service_account_file.return_value = MagicMock()
            client = GoogleSheetsClient("/path/to/creds.json", "test_spreadsheet_id")
            result = client.connect()

        assert result is True
