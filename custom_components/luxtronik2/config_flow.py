import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_IP, CONF_PASSWORD, CONF_PORT, CONF_INTERVAL


class LuxtronikConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Luxtronik2 config flow."""

    VERSION = 1

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Redirect initial step to user step, while enforcing uniqueness."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial user step."""

        # Wenn schon Eingaben vorliegen → Duplikate prüfen
        if user_input is not None:
            # Prüfen ob IP-Adresse schon existiert
            for entry in self._async_current_entries():
                if entry.data.get(CONF_IP) == user_input[CONF_IP]:
                    return self.async_abort(reason="already_configured")

            await self.async_set_unique_id(user_input[CONF_IP])
            self._abort_if_unique_id_configured()
            # Alles ok → Integration anlegen
            return self.async_create_entry(
                title=f"Luxtronik @ {user_input[CONF_IP]}",
                data=user_input,
            )

        # Erstes Anzeigen des Formulars
        data_schema = vol.Schema(
            {
                vol.Required(CONF_IP): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_PORT, default=8214): int,
                vol.Optional(CONF_INTERVAL, default=10): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )
