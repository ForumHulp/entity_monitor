from homeassistant.core import HomeAssistant
from .const import DOMAIN


def async_register(hass: HomeAssistant, register):
    """Register system health info."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant):
    entries = hass.data.get(DOMAIN, {})

    total_entries = len(entries)

    total_entities = 0
    for entry_id in entries:
        sensor = entries[entry_id].get("sensor")
        if sensor:
            total_entities += len(sensor._entities)

    return {
        "config_entries": total_entries,
        "monitored_entities": total_entities,
    }