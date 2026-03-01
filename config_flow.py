import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

DOMAIN = "entity_monitor"


class EntityMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="Entity Monitor",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("entities"): selector.EntitySelector(
                        selector.EntitySelectorConfig(multiple=True)
                    ),
                    vol.Optional("dwains_notifications", default=True): bool,
                }
            ),
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return EntityMonitorOptionsFlow(config_entry)


class EntityMonitorOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_entities = self._config_entry.options.get(
            "entities",
            self._config_entry.data.get("entities", [])
        )

        current_dwains = self._config_entry.options.get(
            "dwains_notifications",
            self._config_entry.data.get("dwains_notifications", True)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "entities",
                        default=current_entities
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(multiple=True)
                    ),
                    vol.Optional("dwains_notifications", default=current_dwains): bool,
                }
            ),
        )