"""Tests for Cat Care Tracker initialization and service handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import date
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.cat_care_tracker import async_setup, async_setup_entry, _async_setup_services
from custom_components.cat_care_tracker.const import (
    DOMAIN,
    CHECKIN_TYPE_FOOD,
    CHECKIN_TYPE_INSULIN,
    CHECKIN_TYPE_WATER,
    CHECKIN_TYPE_BG,
    SERVICE_LOG_FEEDING,
    SERVICE_LOG_INSULIN,
    SERVICE_LOG_WATER,
    SERVICE_LOG_BLOOD_GLUCOSE,
    SERVICE_LOG_ENTRY,
    ATTR_CHECKIN_TYPES,
    ATTR_WATER_REFILL,
    ATTR_BG_LEVEL,
)


@pytest.mark.asyncio
async def test_static_path_registration(hass: HomeAssistant):
    """Test that the static path for frontend resources is registered."""
    # Mock the HTTP component's async_register_static_paths
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()

    # Call async_setup
    result = await async_setup(hass, {})

    # Verify the function returned True
    assert result is True

    # Verify async_register_static_paths was called
    hass.http.async_register_static_paths.assert_called_once()

    # Get the call arguments
    call_args = hass.http.async_register_static_paths.call_args[0][0]

    # Verify the path config
    assert len(call_args) == 1
    path_config = call_args[0]
    assert path_config.url_path == "/cat_care_tracker_static"
    assert "cat_care_tracker/www" in path_config.path
    assert path_config.cache_headers is False


@pytest.mark.asyncio
async def test_service_calls_async_refresh(hass: HomeAssistant):
    """Test that service handlers call async_refresh for immediate updates."""
    # Create a mock config entry
    mock_entry = MagicMock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry_id"
    mock_entry.data = {
        "spreadsheet_id": "test_spreadsheet_id",
        "cat_name": "Whiskers",
    }

    # Create a mock coordinator with async_refresh
    mock_coordinator = MagicMock()
    mock_coordinator.async_refresh = AsyncMock()
    mock_coordinator.async_request_refresh = AsyncMock()
    mock_coordinator.data = {}

    # Create a mock client
    mock_client = MagicMock()
    mock_client.append_entry = MagicMock(return_value=True)

    # Create a mock session
    mock_session = AsyncMock()
    mock_session.async_ensure_token_valid = AsyncMock()
    mock_session.token = {"access_token": "test_token"}

    # Store coordinator and session in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_entry.entry_id] = {
        "coordinator": mock_coordinator,
        "session": mock_session,
        "create_client": lambda: mock_client,
    }

    # Setup services
    await _async_setup_services(hass, mock_entry)

    # Call the log_feeding service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_LOG_FEEDING,
        {},
        blocking=True,
    )

    # Verify that async_refresh was called (not async_request_refresh)
    mock_coordinator.async_refresh.assert_called_once()
    mock_coordinator.async_request_refresh.assert_not_called()

    # Verify the client was called with correct parameters
    mock_client.append_entry.assert_called_once_with(
        [CHECKIN_TYPE_FOOD], None, None, None, None
    )


@pytest.mark.asyncio
async def test_service_handles_failure_gracefully(hass: HomeAssistant):
    """Test that service handlers don't call refresh when append fails."""
    # Create a mock config entry
    mock_entry = MagicMock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry_id"
    mock_entry.data = {
        "spreadsheet_id": "test_spreadsheet_id",
        "cat_name": "Whiskers",
    }

    # Create a mock coordinator with async_refresh
    mock_coordinator = MagicMock()
    mock_coordinator.async_refresh = AsyncMock()
    mock_coordinator.data = {}

    # Create a mock client that fails to append
    mock_client = MagicMock()
    mock_client.append_entry = MagicMock(return_value=False)

    # Create a mock session
    mock_session = AsyncMock()
    mock_session.async_ensure_token_valid = AsyncMock()
    mock_session.token = {"access_token": "test_token"}

    # Store coordinator and session in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_entry.entry_id] = {
        "coordinator": mock_coordinator,
        "session": mock_session,
        "create_client": lambda: mock_client,
    }

    # Setup services
    await _async_setup_services(hass, mock_entry)

    # Call the log_feeding service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_LOG_FEEDING,
        {},
        blocking=True,
    )

    # Verify that async_refresh was NOT called when append fails
    mock_coordinator.async_refresh.assert_not_called()

    # Verify the client was called
    mock_client.append_entry.assert_called_once()


@pytest.mark.asyncio
async def test_log_entry_service_calls_async_refresh(hass: HomeAssistant):
    """Test that log_entry service calls async_refresh."""
    mock_entry = MagicMock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry_id"
    mock_entry.data = {
        "spreadsheet_id": "test_spreadsheet_id",
        "cat_name": "Whiskers",
    }

    mock_coordinator = MagicMock()
    mock_coordinator.async_refresh = AsyncMock()
    mock_coordinator.data = {}

    mock_client = MagicMock()
    mock_client.append_entry = MagicMock(return_value=True)

    mock_session = AsyncMock()
    mock_session.async_ensure_token_valid = AsyncMock()
    mock_session.token = {"access_token": "test_token"}

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_entry.entry_id] = {
        "coordinator": mock_coordinator,
        "session": mock_session,
        "create_client": lambda: mock_client,
    }

    await _async_setup_services(hass, mock_entry)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_LOG_ENTRY,
        {ATTR_CHECKIN_TYPES: [CHECKIN_TYPE_FOOD, CHECKIN_TYPE_INSULIN]},
        blocking=True,
    )

    mock_coordinator.async_refresh.assert_called_once()
    mock_client.append_entry.assert_called_once()


@pytest.mark.asyncio
async def test_log_insulin_service_calls_async_refresh(hass: HomeAssistant):
    """Test that log_insulin service calls async_refresh."""
    mock_entry = MagicMock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry_id"
    mock_entry.data = {
        "spreadsheet_id": "test_spreadsheet_id",
        "cat_name": "Whiskers",
    }

    mock_coordinator = MagicMock()
    mock_coordinator.async_refresh = AsyncMock()
    mock_coordinator.data = {}

    mock_client = MagicMock()
    mock_client.append_entry = MagicMock(return_value=True)

    mock_session = AsyncMock()
    mock_session.async_ensure_token_valid = AsyncMock()
    mock_session.token = {"access_token": "test_token"}

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_entry.entry_id] = {
        "coordinator": mock_coordinator,
        "session": mock_session,
        "create_client": lambda: mock_client,
    }

    await _async_setup_services(hass, mock_entry)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_LOG_INSULIN,
        {},
        blocking=True,
    )

    mock_coordinator.async_refresh.assert_called_once()
    mock_client.append_entry.assert_called_once_with(
        [CHECKIN_TYPE_INSULIN], None, None, None, None
    )


@pytest.mark.asyncio
async def test_log_water_service_calls_async_refresh(hass: HomeAssistant):
    """Test that log_water service calls async_refresh."""
    mock_entry = MagicMock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry_id"
    mock_entry.data = {
        "spreadsheet_id": "test_spreadsheet_id",
        "cat_name": "Whiskers",
    }

    mock_coordinator = MagicMock()
    mock_coordinator.async_refresh = AsyncMock()
    mock_coordinator.data = {}

    mock_client = MagicMock()
    mock_client.append_entry = MagicMock(return_value=True)

    mock_session = AsyncMock()
    mock_session.async_ensure_token_valid = AsyncMock()
    mock_session.token = {"access_token": "test_token"}

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_entry.entry_id] = {
        "coordinator": mock_coordinator,
        "session": mock_session,
        "create_client": lambda: mock_client,
    }

    await _async_setup_services(hass, mock_entry)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_LOG_WATER,
        {ATTR_WATER_REFILL: "250ml"},
        blocking=True,
    )

    mock_coordinator.async_refresh.assert_called_once()
    mock_client.append_entry.assert_called_once_with(
        [CHECKIN_TYPE_WATER], "250ml", None, None, None
    )


@pytest.mark.asyncio
async def test_log_blood_glucose_service_calls_async_refresh(hass: HomeAssistant):
    """Test that log_blood_glucose service calls async_refresh."""
    mock_entry = MagicMock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry_id"
    mock_entry.data = {
        "spreadsheet_id": "test_spreadsheet_id",
        "cat_name": "Whiskers",
    }

    mock_coordinator = MagicMock()
    mock_coordinator.async_refresh = AsyncMock()
    mock_coordinator.data = {}

    mock_client = MagicMock()
    mock_client.append_entry = MagicMock(return_value=True)

    mock_session = AsyncMock()
    mock_session.async_ensure_token_valid = AsyncMock()
    mock_session.token = {"access_token": "test_token"}

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_entry.entry_id] = {
        "coordinator": mock_coordinator,
        "session": mock_session,
        "create_client": lambda: mock_client,
    }

    await _async_setup_services(hass, mock_entry)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_LOG_BLOOD_GLUCOSE,
        {ATTR_BG_LEVEL: 120},
        blocking=True,
    )

    mock_coordinator.async_refresh.assert_called_once()
    mock_client.append_entry.assert_called_once_with(
        [CHECKIN_TYPE_BG], None, 120, None, None
    )
