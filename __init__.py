from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import Platform
from .const import DOMAIN

PLATFORMS = [Platform.SENSOR]

async def async_setup(hass: HomeAssistant, config: dict):
    async def handle_rescan(call: ServiceCall):
        for entry_id in hass.data.get(DOMAIN, {}):
            sensor = hass.data[DOMAIN][entry_id].get("sensor")
            if sensor:
                sensor._initialize_states()
                sensor.async_write_ha_state()

    hass.services.async_register(DOMAIN, "rescan", handle_rescan)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    hass.data[DOMAIN].pop(entry.entry_id)
    return True