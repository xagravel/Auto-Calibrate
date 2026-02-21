"""Sensor platform for Auto-Calibrate."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    ATTR_MAX_RAW,
    ATTR_MIN_RAW,
    ATTR_RAW_VALUE,
    ATTR_SOURCE_ENTITY,
    CONF_NAME,
    CONF_SOURCE_ENTITY,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Auto-Calibrate sensor from a config entry."""
    source_entity: str = entry.data[CONF_SOURCE_ENTITY]
    name: str = entry.data[CONF_NAME]
    entity_id_suffix: str = entry.data.get("entity_id_suffix", f"{source_entity.split('.', 1)[-1]}_calibrated")

    sensor = AutoCalibrateSensor(
        entry_id=entry.entry_id,
        source_entity=source_entity,
        name=name,
        entity_id_suffix=entity_id_suffix,
    )
    async_add_entities([sensor], True)
    hass.data[DOMAIN][entry.entry_id]["sensor"] = sensor


class AutoCalibrateSensor(RestoreSensor):
    """A self-learning sensor that normalizes a raw source to 0-100%."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.MOISTURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_should_poll = False

    def __init__(
        self,
        entry_id: str,
        source_entity: str,
        name: str,
        entity_id_suffix: str,
    ) -> None:
        """Initialize the sensor."""
        self._entry_id = entry_id
        self._source_entity = source_entity
        self._attr_name = name
        self._attr_unique_id = f"auto_calibrate_{source_entity}"
        self.entity_id = f"sensor.{entity_id_suffix}"

        self._min_raw: float | None = None
        self._max_raw: float | None = None
        self._raw_value: float | None = None
        self._unsub: callback | None = None

    async def async_added_to_hass(self) -> None:
        """Restore state and subscribe to source entity changes."""
        await super().async_added_to_hass()

        last_sensor_data = await self.async_get_last_sensor_data()
        last_state = await self.async_get_last_state()

        if last_state is not None:
            attrs = last_state.attributes
            if ATTR_MIN_RAW in attrs and attrs[ATTR_MIN_RAW] is not None:
                self._min_raw = float(attrs[ATTR_MIN_RAW])
            if ATTR_MAX_RAW in attrs and attrs[ATTR_MAX_RAW] is not None:
                self._max_raw = float(attrs[ATTR_MAX_RAW])

        if last_sensor_data is not None and last_sensor_data.native_value is not None:
            try:
                self._attr_native_value = float(last_sensor_data.native_value)
            except (ValueError, TypeError):
                pass

        _LOGGER.debug(
            "Restored min_raw=%s, max_raw=%s for %s",
            self._min_raw,
            self._max_raw,
            self.entity_id,
        )

        current_state = self.hass.states.get(self._source_entity)
        if current_state is not None:
            self._process_raw_value(current_state.state)
            self.async_write_ha_state()

        self._unsub = async_track_state_change_event(
            self.hass, [self._source_entity], self._async_source_state_changed
        )

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from source entity updates."""
        if self._unsub is not None:
            self._unsub()
            self._unsub = None

    @callback
    def _async_source_state_changed(self, event: Event) -> None:
        """Handle state changes from the source sensor."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        self._process_raw_value(new_state.state)
        self.async_write_ha_state()

    def _process_raw_value(self, raw_state: str) -> None:
        """Process a raw state value and update min/max/normalized."""
        try:
            value = float(raw_state)
        except (ValueError, TypeError):
            return

        self._raw_value = value

        if self._min_raw is None or value < self._min_raw:
            self._min_raw = value
            _LOGGER.debug("New min_raw=%s for %s", self._min_raw, self.entity_id)

        if self._max_raw is None or value > self._max_raw:
            self._max_raw = value
            _LOGGER.debug("New max_raw=%s for %s", self._max_raw, self.entity_id)

    @property
    def native_value(self) -> float | None:
        """Return the normalized 0-100% value."""
        if self._raw_value is None or self._min_raw is None or self._max_raw is None:
            return None

        if self._min_raw == self._max_raw:
            return 0.0

        normalized = (
            (self._raw_value - self._min_raw) / (self._max_raw - self._min_raw)
        ) * 100.0

        return round(max(0.0, min(100.0, normalized)), 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return state attributes including learned limits."""
        return {
            ATTR_MIN_RAW: self._min_raw,
            ATTR_MAX_RAW: self._max_raw,
            ATTR_RAW_VALUE: self._raw_value,
            ATTR_SOURCE_ENTITY: self._source_entity,
        }

    @callback
    def reset_calibration(self) -> None:
        """Reset the learned min/max values."""
        _LOGGER.info("Resetting calibration for %s", self.entity_id)
        self._min_raw = None
        self._max_raw = None
        self._raw_value = None
        self.async_write_ha_state()
