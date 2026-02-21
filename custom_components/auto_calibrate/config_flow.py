"""Config flow for Auto-Calibrate Sensor."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers import selector

from .const import CONF_NAME, CONF_SOURCE_ENTITY, DOMAIN


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
                source_state = self.hass.states.get(source_entity)
                if custom_name:
                    name = custom_name
                    entity_id_suffix = custom_name.lower().replace(" ", "_")
                else:
                    if source_state and source_state.attributes.get("friendly_name"):
                        name = source_state.attributes["friendly_name"]
                    else:
                        name = source_entity.split(".", 1)[-1].replace("_", " ").title()
                    source_id = source_entity.split(".", 1)[-1]
                    entity_id_suffix = f"{source_id}_calibrated"
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_SOURCE_ENTITY: source_entity,
                        CONF_NAME: name,
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
