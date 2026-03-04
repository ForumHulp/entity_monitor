from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
):
    sensor = hass.data[DOMAIN][entry.entry_id].get("sensor")

    return {
        "entry_data": entry.data,
        "entry_options": entry.options,
        "monitored_entities": sensor._entities if sensor else [],
        "current_results": sensor._results if sensor else {},
    }