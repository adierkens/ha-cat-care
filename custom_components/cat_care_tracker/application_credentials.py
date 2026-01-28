"""Application credentials for Cat Care Tracker."""
from homeassistant.components.application_credentials import AuthorizationServer
from homeassistant.core import HomeAssistant

AUTHORIZATION_SERVER = AuthorizationServer(
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    token_url="https://oauth2.googleapis.com/token",
)


async def async_get_authorization_server(hass: HomeAssistant) -> AuthorizationServer:
    """Return the authorization server."""
    return AUTHORIZATION_SERVER


async def async_get_description_placeholders(hass: HomeAssistant) -> dict[str, str]:
    """Return description placeholders for the credentials dialog."""
    return {
        "oauth_consent_url": "https://console.cloud.google.com/apis/credentials/consent",
        "more_info_url": "https://github.com/adierkens/ha-google-sheets#configuration",
        "oauth_creds_url": "https://console.cloud.google.com/apis/credentials",
    }
