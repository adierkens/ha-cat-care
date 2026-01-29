"""Cat Care Tracker integration for Home Assistant."""
from __future__ import annotations

from datetime import timedelta, date
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_SPREADSHEET_ID,
    CONF_CAT_NAME,
    CHECKIN_TYPE_FOOD,
    CHECKIN_TYPE_INSULIN,
    CHECKIN_TYPE_WATER,
    CHECKIN_TYPE_BG,
    CHECKIN_TYPES,
    SERVICE_LOG_ENTRY,
    SERVICE_LOG_FEEDING,
    SERVICE_LOG_INSULIN,
    SERVICE_LOG_WATER,
    SERVICE_LOG_BLOOD_GLUCOSE,
    DEFAULT_UPDATE_INTERVAL,
    ATTR_CHECKIN_TYPES,
    ATTR_WATER_REFILL,
    ATTR_BG_LEVEL,
)
from .google_sheets import GoogleSheetsOAuthClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cat Care Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get the OAuth2 implementation and create a session
    implementation = await async_get_config_entry_implementation(hass, entry)
    session = OAuth2Session(hass, entry, implementation)

    # Ensure we have a valid token
    await session.async_ensure_token_valid()

    spreadsheet_id = entry.data[CONF_SPREADSHEET_ID]

    def create_client() -> GoogleSheetsOAuthClient:
        """Create a new client with the current access token."""
        return GoogleSheetsOAuthClient(
            session.token["access_token"],
            spreadsheet_id,
        )

    async def async_update_data() -> dict[str, Any]:
        """Fetch data from Google Sheets."""
        try:
            # Ensure token is valid before making API calls
            await session.async_ensure_token_valid()
            client = create_client()

            # Get last entries for each type
            data = {}

            for checkin_type in CHECKIN_TYPES:
                last_entry = await hass.async_add_executor_job(
                    client.get_last_entry_by_type, checkin_type
                )
                data[f"last_{checkin_type}"] = last_entry

            # Get today's entries and counts
            data["today_entries"] = await hass.async_add_executor_job(
                client.get_entries_for_date, date.today()
            )
            data["today_counts"] = await hass.async_add_executor_job(
                client.get_today_counts
            )

            # Get recent entries
            data["recent_entries"] = await hass.async_add_executor_job(
                client.get_entries, 20
            )

            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Google Sheets: {err}") from err

    # Create the data update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="cat_care_tracker",
        update_method=async_update_data,
        update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator and session
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "session": session,
        "create_client": create_client,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await _async_setup_services(hass, entry)

    return True


async def _async_setup_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up services for Cat Care Tracker."""

    async def get_client() -> GoogleSheetsOAuthClient:
        """Get a client with a valid token."""
        session = hass.data[DOMAIN][entry.entry_id]["session"]
        await session.async_ensure_token_valid()
        return hass.data[DOMAIN][entry.entry_id]["create_client"]()

    async def handle_log_entry(call: ServiceCall) -> None:
        """Handle the log_entry service call."""
        checkin_types = call.data.get(ATTR_CHECKIN_TYPES, [])
        water_refill = call.data.get(ATTR_WATER_REFILL)
        bg_level = call.data.get(ATTR_BG_LEVEL)
        entry_time = call.data.get("time")

        if not checkin_types:
            _LOGGER.error("No check-in types specified")
            return

        client = await get_client()
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

        success = await hass.async_add_executor_job(
            client.append_entry, checkin_types, water_refill, bg_level, None, entry_time
        )

        if success:
            await coordinator.async_refresh()
        else:
            _LOGGER.error("Failed to log entry")

    async def handle_log_feeding(call: ServiceCall) -> None:
        """Handle the log_feeding service call."""
        entry_time = call.data.get("time")
        client = await get_client()
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

        success = await hass.async_add_executor_job(
            client.append_entry, [CHECKIN_TYPE_FOOD], None, None, None, entry_time
        )

        if success:
            await coordinator.async_refresh()
        else:
            _LOGGER.error("Failed to log feeding")

    async def handle_log_insulin(call: ServiceCall) -> None:
        """Handle the log_insulin service call."""
        entry_time = call.data.get("time")
        client = await get_client()
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

        success = await hass.async_add_executor_job(
            client.append_entry, [CHECKIN_TYPE_INSULIN], None, None, None, entry_time
        )

        if success:
            await coordinator.async_refresh()
        else:
            _LOGGER.error("Failed to log insulin")

    async def handle_log_water(call: ServiceCall) -> None:
        """Handle the log_water service call."""
        water_refill = call.data.get(ATTR_WATER_REFILL)
        entry_time = call.data.get("time")
        client = await get_client()
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

        success = await hass.async_add_executor_job(
            client.append_entry, [CHECKIN_TYPE_WATER], water_refill, None, None, entry_time
        )

        if success:
            await coordinator.async_refresh()
        else:
            _LOGGER.error("Failed to log water")

    async def handle_log_blood_glucose(call: ServiceCall) -> None:
        """Handle the log_blood_glucose service call."""
        bg_level = call.data.get(ATTR_BG_LEVEL)
        entry_time = call.data.get("time")
        client = await get_client()
        coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

        if not bg_level:
            _LOGGER.error("Blood glucose level is required")
            return

        success = await hass.async_add_executor_job(
            client.append_entry, [CHECKIN_TYPE_BG], None, bg_level, None, entry_time
        )

        if success:
            await coordinator.async_refresh()
        else:
            _LOGGER.error("Failed to log blood glucose")

    # Register services if not already registered
    if not hass.services.has_service(DOMAIN, SERVICE_LOG_ENTRY):
        hass.services.async_register(
            DOMAIN,
            SERVICE_LOG_ENTRY,
            handle_log_entry,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_CHECKIN_TYPES): vol.All(
                        vol.Coerce(list), [vol.In(CHECKIN_TYPES)]
                    ),
                    vol.Optional(ATTR_WATER_REFILL): vol.Coerce(str),
                    vol.Optional(ATTR_BG_LEVEL): vol.Coerce(int),
                    vol.Optional("time"): vol.Coerce(str),
                }
            ),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_LOG_FEEDING):
        hass.services.async_register(
            DOMAIN,
            SERVICE_LOG_FEEDING,
            handle_log_feeding,
            schema=vol.Schema(
                {
                    vol.Optional("time"): vol.Coerce(str),
                }
            ),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_LOG_INSULIN):
        hass.services.async_register(
            DOMAIN,
            SERVICE_LOG_INSULIN,
            handle_log_insulin,
            schema=vol.Schema(
                {
                    vol.Optional("time"): vol.Coerce(str),
                }
            ),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_LOG_WATER):
        hass.services.async_register(
            DOMAIN,
            SERVICE_LOG_WATER,
            handle_log_water,
            schema=vol.Schema(
                {
                    vol.Optional(ATTR_WATER_REFILL): vol.Coerce(str),
                    vol.Optional("time"): vol.Coerce(str),
                }
            ),
        )

    if not hass.services.has_service(DOMAIN, SERVICE_LOG_BLOOD_GLUCOSE):
        hass.services.async_register(
            DOMAIN,
            SERVICE_LOG_BLOOD_GLUCOSE,
            handle_log_blood_glucose,
            schema=vol.Schema(
                {
                    vol.Required(ATTR_BG_LEVEL): vol.Coerce(int),
                    vol.Optional("time"): vol.Coerce(str),
                }
            ),
        )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
