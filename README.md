<div align="center">

# 🦎 Gecko Integration for Home Assistant

**Control your spa, hot tub, or pool equipment directly from Home Assistant**

[![Version](https://img.shields.io/badge/version-2.2.0-orange.svg?style=for-the-badge)](https://github.com/LogixDE/ha-gecko-integration)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg?style=for-the-badge)](LICENSE)

</div>

> **ℹ️ About this fork:** [LogixDE/ha-gecko-integration](https://github.com/LogixDE/ha-gecko-integration)
> is a community build of the official [Gecko integration](https://github.com/geckoal/ha-gecko-integration).
> It bundles fixes and features from open upstream pull requests (stability, telemetry,
> RGB lighting, heat pump status) so you can use them today. See
> [What's in this build](#-whats-in-this-build) for details and credits.

---

## ✨ Features

<table>
<tr>
<td width="33%" valign="top">

### 🌡️ Climate Control
- Set target temperature
- Monitor current temperature
- Heating, cooling and defrost status
- **Heat source:** heat pump, electric or both
- **Heat pump error** detection
- **Eco mode** status
- **Watercare mode as preset** right in the thermostat

</td>
<td width="33%" valign="top">

### 💡 Lighting
- Multi-zone LED control
- **RGB color** and **brightness**
- **Light effects** (learned from the spa)
- Stable color state, no flicker on slider drags

</td>
<td width="33%" valign="top">

### 💨 Pumps & Fans
- Pumps, blowers and waterfalls
- Speed presets for multi-speed pumps
- Single-speed pumps: plain on/off
- **Real running state**, including automatic runs
- **Filtration-safe:** turn-off never interrupts filtration, heating or flow check

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 🔄 Watercare Modes
- Away mode
- Standard mode
- Energy savings mode
- Weekender mode

</td>
<td width="33%" valign="top">

### 📊 Monitoring
- Gateway, spa and cloud connection
- Filtration, flow check, heating, spa in use
- Firmware, serial numbers, RF signal
- Pump speed modes and flow status

</td>
<td width="33%" valign="top">

### ☁️ Cloud Integration
- Secure OAuth2 login
- AWS IoT backend (push, no polling)
- Automatic discovery
- **Robust reconnects** without stale entities

</td>
</tr>
</table>

---

## 📦 Installation

### Method 1: HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Navigate to **Integrations**
3. Click the **⋮** menu (top right) → **Custom repositories**
4. Add repository URL: `https://github.com/LogixDE/ha-gecko-integration`
5. Select category: **Integration**
6. Click **Download** on the Gecko integration
7. **Restart Home Assistant**

> **Switching from the official integration?** Remove `geckoal/ha-gecko-integration`
> (and any other HACS repository that installs into `custom_components/gecko`) in HACS
> first, then download this repository and restart. Your existing config entry and
> entities are kept. New pushes to `main` show up as updates in HACS.

### Method 2: Manual Installation

1. Download the [repository as ZIP](https://github.com/LogixDE/ha-gecko-integration/archive/refs/heads/main.zip)
2. Extract and copy the `custom_components/gecko` folder to your Home Assistant `custom_components` directory
3. Your directory structure should look like:
   ```
   config/
   └── custom_components/
       └── gecko/
           ├── __init__.py
           ├── manifest.json
           └── ...
   ```
4. **Restart Home Assistant**

---

## ⚙️ Setup & Configuration

### Initial Setup

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **"Gecko"**
4. Click on the Gecko integration

### Authentication

The integration will guide you through OAuth2 authentication:

1. Click **Continue** to begin the OAuth flow
2. You'll be redirected to the Gecko login page
3. Enter your **Gecko spa account credentials**
4. Grant permission to Home Assistant
5. You'll be redirected back automatically

### Automatic Discovery

Once authenticated:
- Your spa(s) will be **automatically discovered**
- All available entities will be created
- Devices appear under **Settings** → **Devices & Services** → **Gecko**

---

## 🎛️ Available Entities

The integration creates multiple entity types for comprehensive spa control:

| Entity Type | Description | Example |
|------------|-------------|---------|
| **Climate** | Temperature control and monitoring | Set spa to 104°F (40°C) |
| **Light** | LED lighting control with brightness | Adjust ambient lighting |
| **Fan** | Pump and blower speed control | Set pump to High speed |
| **Binary Sensor** | Connection, heating, filtration, eco mode | Filtration running |
| **Sensor** | Telemetry, firmware, RF, pump speed modes | RF signal strength |
| **Select** | Watercare mode | Switch to Energy Savings mode |

### Entity Examples

**Climate Entity:**
- `climate.spa_name_thermostat_1` - Main temperature control

  Presets: the watercare mode (`Away`, `Standard`, `Savings`, `Super Savings`,
  `Weekender`) can be chosen directly in the thermostat. It is the same setting as the
  watercare mode select entity.

  Extra attributes:
  | Attribute | Meaning |
  |-----------|---------|
  | `hvac_action` | `heating`, `cooling` (heat pump actively cooling), `defrosting` or `idle`, mapped from the full device status. Water that is above the set point and cools down by itself shows as `idle` |
  | `heat_source` | `heat_pump`, `electric`, `heat_pump_and_electric` or `none` |
  | `heat_pump_error` | `true` when the device reports a heat pump fault |
  | `eco_mode` | Eco flag of the temperature zone |

**Light Entities:**
- `light.spa_name_light_1` - Lighting zone with RGB color, brightness and effects

  Effects are not hardcoded: the list grows as the spa reports effects, so only
  effects your controller actually supports are offered.

**Fan Entities:**
- `fan.spa_name_pump_1` - Main circulation pump
- `fan.spa_name_pump_2` - Jet pump
- `fan.spa_name_waterfall` - Waterfall

  Speeds are only offered when the pump supports them. Single-speed pumps (configured
  speed range with minimum = maximum) are plain on/off switches.

  The fan state shows whether the pump is **physically running**, whatever started it.
  Turning a pump off is ignored while the spa itself needs the flow (filtration,
  heating, heat pump, flow check), so automations cannot interrupt those cycles.

  Extra attributes:
  | Attribute | Meaning |
  |-----------|---------|
  | `user_controlled` | `true` when the pump runs because you started it |
  | `initiators` | Everything currently requesting this pump (e.g. `UD`, `FI`, `CF`, `HTP`) |
  | `automatic_initiators` | The non-user part of `initiators` |
  | `filtration_active` / `checkflow_active` | Filtration or flow check uses this pump |
  | `physical_speed` / `physical_percentage` | Actual speed reported by the spa |

**Sensors:**
- `sensor.spa_name_rf_signal_strength` - RF signal strength
- `sensor.spa_name_rf_channel` - RF channel
- `sensor.spa_name_pack_configuration` - Spa pack configuration identifier
- `sensor.spa_name_home_en_firmware_version` - Home (EN) firmware version
- `sensor.spa_name_home_en_serial_number` - Home (EN) serial number
- `sensor.spa_name_spa_co_firmware_version` - Spa (CO) firmware version
- `sensor.spa_name_spa_co_serial_number` - Spa (CO) serial number
- `sensor.spa_name_raw_api_data` - credential-redacted raw API payloads for debugging (disabled by default)
- `sensor.spa_name_water_temperature_1_flow_status` - Flow status: `OK`, `Flow check in progress` (code `IP`) or `Other`; the raw code is in the `raw_code` attribute (German translation included)
- `sensor.spa_name_water_temperature_1_status` - Temperature zone status (`HEATING`, `HEAT_PUMP_HEATING`, `COOLING`, …)
- `sensor.spa_name_pump_1_speed_mode` - Speed mode per pump / waterfall (`off`, `low`, `high`, …; `on` for single-speed pumps)

**Binary Sensors:**
- `binary_sensor.spa_name_gateway_status` - Gateway online
- `binary_sensor.spa_name_spa_status` - Spa controller running
- `binary_sensor.spa_name_transport_connection` - Cloud (MQTT) connection
- `binary_sensor.spa_name_overall_connection` - All of the above
- `binary_sensor.spa_name_spa_in_use` - Someone is using the spa (user-started pumps, lights, …)
- `binary_sensor.spa_name_eco_mode_1` - Eco mode of temperature zone 1
- `binary_sensor.spa_name_heating` - Vessel-level heating state (on when any temperature zone is heating)
- `binary_sensor.spa_name_heating_1` - Temperature zone 1 heating state
- `binary_sensor.spa_name_filtration` - Automatic filtration state (on for `FI`)
- `binary_sensor.spa_name_flow_check` - Automatic flow-check state (on for `CF` and recorded in entity history)

---

## 🧩 What's in this build

On top of the official integration (2.1.1), this build contains:

| Source | Change |
|--------|--------|
| upstream [#63](https://github.com/geckoal/ha-gecko-integration/pull/63) / [#64](https://github.com/geckoal/ha-gecko-integration/pull/64) (David Lacroix) | Old client is stopped on every reconnect, entities follow the new client instead of freezing, active pump without speed no longer breaks updates, test suite and CI |
| upstream [#37](https://github.com/geckoal/ha-gecko-integration/pull/37) (Karl G) | No more brief `unavailable` on partial shadow updates, filtration-safe pump control, telemetry sensors and binary sensors, low-speed pump fix |
| upstream [#54](https://github.com/geckoal/ha-gecko-integration/pull/54) (Marek O) | Fixes Auth0 "Callback URL mismatch" |
| upstream [#56](https://github.com/geckoal/ha-gecko-integration/pull/56), [#57](https://github.com/geckoal/ha-gecko-integration/pull/57), [#60](https://github.com/geckoal/ha-gecko-integration/pull/60) (Fabian Harder) | Eco mode attribute, RGB color / brightness / effects, heat source and heat pump error, correct HVAC action mapping |
| gecko-iot-client [#11](https://github.com/geckoal/gecko-iot-client/pull/11), [#12](https://github.com/geckoal/gecko-iot-client/pull/12), [#13](https://github.com/geckoal/gecko-iot-client/pull/13) | Applied at runtime to gecko-iot-client 1.0.3 (`client_patches.py`): speed presets for multi-speed pumps, JSON-safe `set_color()`, "Super Savings" watercare mode accepted |
| this build | Readable flow status, watercare mode as thermostat preset (updates instantly), pumps show their real running state again, single-speed pumps are on/off only, AWS CRT check moved off the event loop |

### Known limitations

- **Heat pump mode** (Eco Heat, Smart Heat, Eco Auto, Smart Auto, Cool, Electric) can be
  changed in the Gecko app, but not through this integration. Gecko's third-party cloud
  session only grants access to the `state` shadow, which does not contain this setting.
  The current heat source is visible via the climate entity's `heat_source` attribute.
- **Eco mode** is read-only. The spa derives it from the watercare mode, so change the
  watercare mode (select entity) instead.

---

## 🆘 Troubleshooting

### Common Issues

**Integration not appearing:**
- Ensure you've restarted Home Assistant after installation
- Check that the `custom_components/gecko` folder exists
- Review Home Assistant logs for errors

**OAuth authentication fails:**
- Verify your Gecko account credentials
- Check internet connectivity
- Try clearing browser cache and retry

**No devices discovered:**
- Confirm your spa is online in the Gecko mobile app
- Wait 1-2 minutes for discovery to complete
- Check that your spa uses Gecko in.touch 3 / in.touch 3+ or compatible system

**Entities not updating:**
- Check RF signal strength sensor (low signal affects updates)
- Verify gateway connectivity in the Gecko app
- Restart the integration: **Settings** → **Devices & Services** → **Gecko** → **⋮** → **Reload**

**Home Assistant restarts or crashes while Gecko connects:**
- Gecko 2.1.2 and newer install a matched AWS IoT runtime; Gecko 2.1.3 limits the hard safety check to Python 3.14+ on ARM64, where the native crash occurs
- Update Gecko through HACS, then perform a full Home Assistant restart
- If the first start reports mixed AWS CRT modules, restart Home Assistant once more; do not use integration reload
- If Core cannot remain running, start Home Assistant in Safe Mode, update Gecko, and then restart normally

---

## 🧪 Development

The tests run against a real Home Assistant through
[pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)
and the real `gecko-iot-client` zone models. Only the MQTT transport and the
IoT client are faked, so no test touches the network.

```bash
python3.14 -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/python -m pytest
```

`requirements_test.txt` pins the Home Assistant release the tests run against.
Bump it with the integration's own minimum version.

---

## 💬 Support & Community

- 🐛 **Issues with this build:** [LogixDE/ha-gecko-integration](https://github.com/LogixDE/ha-gecko-integration/issues)
- 🦎 **Official integration:** [geckoal/ha-gecko-integration](https://github.com/geckoal/ha-gecko-integration)

---

## 🙏 Credits

This integration is built by [Gecko Alliance](https://github.com/geckoal) with the
[gecko-iot-client](https://github.com/geckoal/gecko-iot-client) library. Thanks to all
contributors whose pull requests are included in this build: Karl G, David Lacroix,
Marek O and Jim Wood, Chris Moore (gecko-iot-client).

---

## 📄 License

Copyright © 2025-2026 Gecko Alliance

Licensed under the Apache License 2.0 - see [LICENSE](LICENSE) for details.

> **⚠️ Important:** This software is intended for personal use with Gecko Alliance equipment through Home Assistant. Commercial use or use outside the intended scope may require authorization from Gecko Alliance. See [NOTICE](NOTICE) for trademark information and usage restrictions.
