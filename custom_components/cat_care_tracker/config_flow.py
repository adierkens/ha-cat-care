"""Config flow for Cat Care Tracker integration."""
from __future__ import annotations

import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_SPREADSHEET_ID,
    CONF_CREDENTIALS_FILE,
    CONF_CAT_NAME,
)
from .google_sheets import GoogleSheetsClient

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input and test the connection."""
    credentials_file = data[CONF_CREDENTIALS_FILE]
    spreadsheet_id = data[CONF_SPREADSHEET_ID]

    # Check if credentials file exists
    if not os.path.isfile(credentials_file):
        raise InvalidCredentials("Credentials file not found")

    # Try to connect to Google Sheets
    client = GoogleSheetsClient(credentials_file, spreadsheet_id)

    # Run connection test in executor to avoid blocking
    connected = await hass.async_add_executor_job(client.connect)

    if not connected:
        raise CannotConnect("Failed to connect to Google Sheets")

    return {"title": f"Cat Care Tracker - {data.get(CONF_CAT_NAME, 'My Cat')}"}


class CatCareTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cat Care Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                # Check if this spreadsheet is already configured
                await self.async_set_unique_id(user_input[CONF_SPREADSHEET_ID])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidCredentials:
                errors["base"] = "invalid_credentials"
            except InvalidSpreadsheet:
                errors["base"] = "invalid_spreadsheet"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # Default values for the form
        default_credentials = "/config/cat_care_tracker_credentials.json"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_SPREADSHEET_ID): cv.string,
                vol.Required(
                    CONF_CREDENTIALS_FILE, default=default_credentials
                ): cv.string,
                vol.Required(CONF_CAT_NAME, default="My Cat"): cv.string,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> CatCareTrackerOptionsFlow:
        """Get the options flow for this handler."""
        return CatCareTrackerOptionsFlow(config_entry)


class CatCareTrackerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Cat Care Tracker."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_cat_name = self.config_entry.data.get(CONF_CAT_NAME, "My Cat")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CAT_NAME, default=current_cat_name): cv.string,
                }
            ),
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidCredentials(Exception):
    """Error to indicate invalid credentials."""


class InvalidSpreadsheet(Exception):
    """Error to indicate invalid spreadsheet."""
