import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.core import callback
from homeassistant.const import STATE_UNKNOWN
from .const import DOMAIN, NAME, MANUFACTURER, MODEL

_LOGGER = logging.getLogger(__name__)


UNAVAILABLE_STATES = {"unavailable", "unknown"}
SCAN_INTERVAL = timedelta(seconds=2)


async def async_setup_entry(hass, entry, async_add_entities):
    sensor = EntityMonitorSensor(hass, entry)

    hass.data[DOMAIN][entry.entry_id]["sensor"] = sensor

    async_add_entities([sensor], True)

class EntityMonitorSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Entity Monitor"

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry

        # Monitoring data
        self._entities = []
        self._results = {}
        self._notified_entities = set()

        # Display rotation
        self._current_index = 0
        self._current_entity = None

        # Listeners
        self._unsub_state_listener = None
        self._unsub_scan_listener = None
        self._unsub_options_listener = None

        self._dwains_enabled = self._get_dwains_enabled()

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------
    @property
    def unique_id(self):
        return f"{DOMAIN}_{self.entry.entry_id}"

    @property
    def native_value(self):
        """Rotating scanning display."""
        if not self._entities or self._current_entity is None:
            return STATE_UNKNOWN

        return (
            f"Scanning: {self._current_entity} "
            f"({self._current_index + 1}/{len(self._entities)})"
        )

    @property
    def extra_state_attributes(self):
        unavailable = [
            entity_id
            for entity_id, state in self._results.items()
            if state in UNAVAILABLE_STATES or state == "not_found"
        ]

        return {
            "total_entities": len(self._entities),
            "unavailable_count": len(unavailable),
            "unavailable_entities": unavailable,
            "current_entity": self._current_entity,
            "entities": [
                {
                    "entity_id": entity_id,
                    "state": self._results.get(entity_id, STATE_UNKNOWN),
                }
                for entity_id in self._entities
            ],
        }

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": NAME,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "sw_version": self.entry.version,
            "entry_type": "service",
        }


    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    async def async_added_to_hass(self):
        self._reload_config()
        self._setup_state_listener()
        self._initialize_states()
        self._setup_scan_rotation()

        self._unsub_options_listener = self.entry.add_update_listener(
            self._async_options_updated
        )

    async def async_will_remove_from_hass(self):
        if self._unsub_state_listener:
            self._unsub_state_listener()

        if self._unsub_scan_listener:
            self._unsub_scan_listener()

        if self._unsub_options_listener:
            self._unsub_options_listener()

    # --------------------------------------------------
    # Config Handling
    # --------------------------------------------------

    def _get_dwains_enabled(self):
        return self.entry.options.get(
            "dwains_notifications",
            self.entry.data.get("dwains_notifications", True),
        )

    def _reload_config(self):
        entities = (
            self.entry.options.get("entities")
            or self.entry.data.get("entities")
            or []
        )

        if isinstance(entities, str):
            entities = [entities]

        self._entities = sorted(set(entities))
        self._dwains_enabled = self._get_dwains_enabled()

        self._current_index = 0
        self._current_entity = None

    async def _async_options_updated(self, hass, entry):
        _LOGGER.debug("Entity Monitor options updated")

        if self._unsub_state_listener:
            self._unsub_state_listener()

        self._reload_config()
        self._setup_state_listener()
        self._initialize_states()

    # --------------------------------------------------
    # State Monitoring (Event Based)
    # --------------------------------------------------

    def _setup_state_listener(self):
        if not self._entities:
            return

        self._unsub_state_listener = async_track_state_change_event(
            self.hass,
            self._entities,
            self._async_state_changed,
        )

    def _initialize_states(self):
        for entity_id in self._entities:
            state_obj = self.hass.states.get(entity_id)

            if state_obj is None:
                self._results[entity_id] = "not_found"
            else:
                self._results[entity_id] = state_obj.state

        self.async_write_ha_state()

    @callback
    def _async_state_changed(self, event):
        entity_id = event.data["entity_id"]
        new_state = event.data.get("new_state")

        if new_state is None:
            entity_state = "not_found"
        else:
            entity_state = new_state.state

        self._results[entity_id] = entity_state

        if self._dwains_enabled:
            self.hass.async_create_task(
                self._handle_notifications(entity_id, entity_state)
            )

        self.async_write_ha_state()

    # --------------------------------------------------
    # UI Rotation (Lightweight)
    # --------------------------------------------------

    def _setup_scan_rotation(self):
        if not self._entities:
            return

        self._unsub_scan_listener = async_track_time_interval(
            self.hass,
            self._async_rotate_display,
            SCAN_INTERVAL,
        )

    async def _async_rotate_display(self, now=None):
        if not self._entities:
            return

        if self._current_index >= len(self._entities):
            self._current_index = 0

        self._current_entity = self._entities[self._current_index]

        self._current_index += 1
        if self._current_index >= len(self._entities):
            self._current_index = 0

        self.async_write_ha_state()

    # --------------------------------------------------
    # Notifications
    # --------------------------------------------------

    async def _handle_notifications(self, entity_id, entity_state):
        notification_id = f"entity_monitor_{entity_id}"

        if entity_state in UNAVAILABLE_STATES or entity_state == "not_found":
            if entity_id in self._notified_entities:
                return

            if self.hass.services.has_service(
                "dwains_dashboard", "notification_create"
            ):
                await self.hass.services.async_call(
                    "dwains_dashboard",
                    "notification_create",
                    {
                        "notification_id": notification_id,
                        "title": "Entity Unavailable",
                        "message": f"{entity_id} is unavailable",
                    },
                    blocking=True,
                )

            self._notified_entities.add(entity_id)

        else:
            if entity_id not in self._notified_entities:
                return

            if self.hass.services.has_service(
                "dwains_dashboard", "notification_dismiss"
            ):
                await self.hass.services.async_call(
                    "dwains_dashboard",
                    "notification_dismiss",
                    {"notification_id": notification_id},
                    blocking=True,
                )

            self._notified_entities.remove(entity_id)