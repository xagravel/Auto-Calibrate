"""Auto-Calibrate Sensor Integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import CONF_ENTITY_ID, DOMAIN, SERVICE_RESET

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Auto-Calibrate from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_reset(call: ServiceCall) -> None:
        """Handle the reset service call."""
        entity_ids: list[str] = call.data[CONF_ENTITY_ID]
        for entity_id in entity_ids:
            for entry_data in hass.data[DOMAIN].values():
                sensor = entry_data.get("sensor")
                if sensor is not None and sensor.entity_id == entity_id:
                    sensor.reset_calibration()

    if not hass.services.has_service(DOMAIN, SERVICE_RESET):
        hass.services.async_register(
            DOMAIN,
            SERVICE_RESET,
            handle_reset,
            schema=vol.Schema(
                {
                    vol.Required(CONF_ENTITY_ID): cv.entity_ids,
                }
            ),
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, SERVICE_RESET)

    return unload_ok
