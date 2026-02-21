# Auto-Calibrate Sensor

A Home Assistant custom integration that creates self-learning sensors. It observes a raw numeric sensor (e.g., a Tuya TS0601 soil moisture probe), dynamically learns its minimum and maximum values over time, and outputs a normalized 0–100% measurement.

## Why?

Many generic sensors report arbitrary raw values with no standardized scale. Instead of manually figuring out offsets and hardcoding them in YAML, this integration watches the sensor over time, remembers the lowest and highest readings it has ever seen, and uses those to calculate a clean percentage.

## Features

- **UI Configuration** — Set up entirely through the Home Assistant UI (Settings > Devices & Services). No YAML required.
- **Self-Learning Limits** — Continuously tracks the all-time minimum and maximum raw values from your source sensor.
- **0–100% Normalization** — Converts the current raw reading into a percentage based on the learned range.
- **State Persistence** — Learned min/max values survive Home Assistant reboots.
- **Reset Service** — Call `auto_calibrate.reset` to clear learned values when moving a probe to a new environment.

## Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations** and click the three-dot menu in the top right.
3. Select **Custom repositories**.
4. Add this repository URL and select **Integration** as the category.
5. Click **Add**, then find "Auto-Calibrate Sensor" in the HACS store and install it.
6. Restart Home Assistant.

### Manual Installation

1. Copy the `custom_components/auto_calibrate/` directory into your Home Assistant `config/custom_components/` folder.
2. Restart Home Assistant.

## Setup

1. Go to **Settings > Devices & Services**.
2. Click **Add Integration** and search for "Auto-Calibrate Sensor".
3. Select the source sensor entity you want to calibrate (must be a numeric sensor).
4. Optionally set a friendly name.
5. Click **Submit**.

The integration will immediately start tracking your source sensor. As it sees new highs and lows, it refines its calibration range automatically.

## How It Works

1. The integration subscribes to state changes on your chosen source sensor.
2. Each time a new value arrives, it checks whether it's a new minimum or maximum.
3. The normalized output is calculated as:

   ```
   percentage = ((current - min) / (max - min)) * 100
   ```

   The result is clamped to 0–100%.

4. On reboot, the learned min/max values are restored from Home Assistant's state registry.

## Attributes

The calibrated sensor exposes the following state attributes:

| Attribute | Description |
|---|---|
| `min_raw` | The lowest raw value seen so far |
| `max_raw` | The highest raw value seen so far |
| `raw_value` | The current raw value from the source sensor |
| `source_entity` | The entity ID of the source sensor |

## Reset Service

To clear the learned calibration data (e.g., when moving a probe to a different plant):

1. Go to **Developer Tools > Services**.
2. Select `auto_calibrate.reset`.
3. Choose the calibrated sensor entity to reset.
4. Click **Call Service**.

The sensor will begin learning new min/max values from scratch.

## Example Use Case

You have a Tuya soil moisture probe that reports values like 26 (dry) to 94 (wet), but these numbers are meaningless on their own. After adding the probe as a source sensor:

- The integration observes 26 as the minimum and 94 as the maximum over time.
- A current reading of 60 would display as **50%** moisture.
- If the probe later reports 20, the minimum updates and all future percentages adjust accordingly.

## License

MIT
