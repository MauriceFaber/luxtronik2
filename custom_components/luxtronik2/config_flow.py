from homeassistant import config_entries
import voluptuous as vol

from .const import DOMAIN, CONF_IP, CONF_PASSWORD, CONF_PORT, DEFAULT_PORT


class LuxtronikConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Luxtronik2."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # Optional: prüfen ob IP erreichbar ist
            # => könnte hier implementiert werden

            return self.async_create_entry(
                title=f"Luxtronik @ {user_input[CONF_IP]}",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_IP): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)
