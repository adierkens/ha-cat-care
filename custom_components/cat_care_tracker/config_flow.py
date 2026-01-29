"""Config flow for Cat Care Tracker integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.config_entry_oauth2_flow import (
    AbstractOAuth2FlowHandler,
)

from .const import (
    DOMAIN,
    CONF_SPREADSHEET_ID,
    CONF_CAT_NAME,
    CONF_SHEET_NAME,
)

_LOGGER = logging.getLogger(__name__)

# Google Sheets API scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class CatCareTrackerOAuth2FlowHandler(
    AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle OAuth2 config flow for Cat Care Tracker."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data that needs to be appended to the authorize url."""
        return {
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        return await self.async_step_pick_implementation(user_input)

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> FlowResult:
        """Create an entry for the flow after OAuth completes."""
        # After OAuth, we need to collect additional information
        self._oauth_data = data
        return await self.async_step_configure()

    async def async_step_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure spreadsheet and cat name after OAuth."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the spreadsheet ID by attempting to access it
            try:
                from .google_sheets import GoogleSheetsOAuthClient

                # Sanitize spreadsheet ID - strip whitespace
                spreadsheet_id = user_input[CONF_SPREADSHEET_ID].strip()
                sheet_name = user_input.get(CONF_SHEET_NAME, "Sheet1").strip()
                
                client = GoogleSheetsOAuthClient(
                    self._oauth_data["token"]["access_token"],
                    spreadsheet_id,
                    sheet_name,
                )

                # Test connection
                connected, error_code = await self.hass.async_add_executor_job(client.test_connection)
                if not connected:
                    # Map error codes to user-friendly error messages
                    if error_code == "not_found":
                        errors["base"] = "spreadsheet_not_found"
                    elif error_code == "permission_denied":
                        errors["base"] = "no_permission"
                    elif error_code == "invalid_credentials":
                        errors["base"] = "invalid_auth"
                    else:
                        errors["base"] = "cannot_connect"
                else:
                    # Check if this spreadsheet is already configured
                    await self.async_set_unique_id(spreadsheet_id)
                    self._abort_if_unique_id_configured()

                    # Merge OAuth data with user config (use sanitized spreadsheet_id)
                    entry_data = {
                        **self._oauth_data,
                        CONF_SPREADSHEET_ID: spreadsheet_id,
                        CONF_CAT_NAME: user_input.get(CONF_CAT_NAME, "My Cat"),
                        CONF_SHEET_NAME: sheet_name,
                    }

                    return self.async_create_entry(
                        title=f"Cat Care Tracker - {entry_data[CONF_CAT_NAME]}",
                        data=entry_data,
                    )

            except Exception:
                _LOGGER.exception("Unexpected exception during configuration")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="configure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SPREADSHEET_ID): cv.string,
                    vol.Required(CONF_CAT_NAME, default="My Cat"): cv.string,
                    vol.Optional(CONF_SHEET_NAME, default="Sheet1"): cv.string,
                }
            ),
            errors=errors,
            description_placeholders={
                "spreadsheet_url": "https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit"
            },
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
            # Update the config entry data with the new cat name and sheet name
            new_data = {**self.config_entry.data, **user_input}
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=new_data
            )
            return self.async_create_entry(title="", data=user_input)

        current_cat_name = self.config_entry.data.get(CONF_CAT_NAME, "My Cat")
        current_sheet_name = self.config_entry.data.get(CONF_SHEET_NAME, "Sheet1")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CAT_NAME, default=current_cat_name): cv.string,
                    vol.Optional(CONF_SHEET_NAME, default=current_sheet_name): cv.string,
                }
            ),
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidCredentials(Exception):
    """Error to indicate invalid credentials."""


class InvalidSpreadsheet(Exception):
    """Error to indicate invalid spreadsheet."""
