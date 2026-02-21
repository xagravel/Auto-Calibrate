# Auto-Calibrate Sensor Integration

## Overview
A Home Assistant custom component that creates self-learning sensors. It observes a raw numeric sensor (e.g., a Tuya soil moisture probe), dynamically learns its minimum and maximum values over time, and outputs a normalized 0-100% measurement.

## Project Architecture

### Directory Structure
```
custom_components/auto_calibrate/
├── __init__.py          # Integration setup, service registration
├── config_flow.py       # UI-based configuration flow
├── const.py             # Constants and domain definition
├── manifest.json        # Integration metadata
├── sensor.py            # Core sensor logic (RestoreEntity-based)
├── services.yaml        # Service definitions for HA UI
└── translations/
    └── en.json          # English UI strings
```

### Key Components
- **const.py**: Defines `DOMAIN = "auto_calibrate"` and all shared constants
- **__init__.py**: Handles `async_setup_entry` / `async_unload_entry`, registers the `auto_calibrate.reset` service
- **config_flow.py**: Provides UI config flow (Settings > Devices & Services) to select a source sensor entity
- **sensor.py**: `AutoCalibrateSensor` extends `RestoreSensor`. Tracks min/max raw values, normalizes to 0-100%, persists state across reboots. Includes entity_id migration logic to ensure correct `[source_id]_calibrated` naming
- **services.yaml**: Defines the `reset` service schema for the HA services UI
- **translations/en.json**: English strings for config flow and services

### How It Works
1. User adds integration via HA UI and selects a source sensor
2. The integration subscribes to state changes on the source entity
3. On each state change, it updates internal `min_raw` / `max_raw` if a new extreme is seen
4. `native_value` returns `((current - min) / (max - min)) * 100`, clamped to 0-100%
5. On HA reboot, `RestoreEntity` restores the learned min/max from the state registry
6. The `auto_calibrate.reset` service clears learned values for re-calibration

### Validation
- Run `python validate.py` to check file structure, Python syntax, JSON validity, and component architecture

## Installation (in Home Assistant)
1. Copy the `custom_components/auto_calibrate/` directory into your HA `config/custom_components/` folder
2. Restart Home Assistant
3. Go to Settings > Devices & Services > Add Integration > "Auto-Calibrate Sensor"
4. Select the source sensor entity and optionally set a friendly name

## Recent Changes
- 2026-02-21: Added entity_id registry migration (both pre-registration and post-registration) to auto-correct entity_ids to `[source_id]_calibrated` format
- 2026-02-21: Set default `suggested_display_precision=1` for percentage output when source entity has no explicit precision setting
- 2026-02-21: Initial implementation with config flow, self-learning sensor, state persistence, and reset service
