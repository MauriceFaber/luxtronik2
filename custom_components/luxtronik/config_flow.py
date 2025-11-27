import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_IP, CONF_PASSWORD

class LuxtronikConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=f"Luxtronik @ {user_input[CONF_IP]}",
                data=user_input,
            )

        schema = vol.Schema({
            vol.Required(CONF_IP): str,
            vol.Required(CONF_PASSWORD): str,
        })

        return self.async_show_form(step_id="user", data_schema=schema)
