"""Config flow for Auto-Calibrate Sensor."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import entity_registry as er, device_registry as dr, selector

from .const import CONF_NAME, CONF_SOURCE_ENTITY, DOMAIN

CONF_CUSTOM_NAME = "custom_name"


class AutoCalibrateConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Auto-Calibrate Sensor."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            source_entity: str = user_input[CONF_SOURCE_ENTITY]

            await self.async_set_unique_id(source_entity)
            self._abort_if_unique_id_configured()

            state = self.hass.states.get(source_entity)
            if state is None:
                errors["base"] = "entity_not_found"
            else:
                try:
                    float(state.state)
                except (ValueError, TypeError):
                    if state.state not in ("unavailable", "unknown"):
                        errors["base"] = "not_numeric"

            if not errors:
                custom_name = user_input.get(CONF_NAME, "").strip()
                source_id = source_entity.split(".", 1)[-1]
                entity_id_suffix = f"{source_id}_calibrated"

                ent_reg = er.async_get(self.hass)
                source_entry = ent_reg.async_get(source_entity)
                source_device_identifiers: list[list[str]] = []
                source_device_connections: list[list[str]] = []

                if source_entry is not None and source_entry.device_id:
                    dev_reg = dr.async_get(self.hass)
                    source_device = dev_reg.async_get(source_entry.device_id)
                    if source_device is not None:
                        if source_device.identifiers:
                            source_device_identifiers = [
                                list(i) for i in source_device.identifiers
                            ]
                        if source_device.connections:
                            source_device_connections = [
                                list(c) for c in source_device.connections
                            ]

                if custom_name:
                    name = custom_name
                    title = custom_name
                else:
                    source_state = self.hass.states.get(source_entity)
                    if source_state and source_state.attributes.get("friendly_name"):
                        name = source_state.attributes["friendly_name"]
                    else:
                        name = source_id.replace("_", " ").title()
                    title = name

                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_SOURCE_ENTITY: source_entity,
                        CONF_NAME: name,
                        CONF_CUSTOM_NAME: custom_name,
                        "source_device_identifiers": source_device_identifiers,
                        "source_device_connections": source_device_connections,
                        "entity_id_suffix": entity_id_suffix,
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_NAME, default=""): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
