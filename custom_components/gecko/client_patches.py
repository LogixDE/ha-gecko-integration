"""Runtime fixes for gecko-iot-client that are not released upstream yet.

Each fix mirrors an open pull request in geckoal/gecko-iot-client. They are
applied only to the client versions listed in PATCHED_VERSIONS, so a newer
client release (which hopefully contains the fixes) is left untouched and
this module can then simply be deleted.

- #11 Preserve the speed range (SpeedConfig) of flow zones so multi-speed
      pumps expose presets, and keep FlowZone.speed a scalar.
- #12 LightingZone.set_color() published its internal RGB object, which is
      not JSON serializable. Publish the list format [r, g, b, i] the device
      itself reports (and which the light entity uses as well).
- #13 OperationModeController.set_mode_by_name() rejected "Super Savings"
      because the space was not mapped to an underscore.
"""

from __future__ import annotations

import functools
import logging
from importlib.metadata import PackageNotFoundError, version
from typing import Any

_LOGGER = logging.getLogger(__name__)

PATCHED_VERSIONS = frozenset({"1.0.3"})

_SCALAR_VALUE_KEYS = ("value", "currentValue", "default", "initialValue")

_applied = False


def apply_client_patches() -> None:
    """Apply all fixes once. Safe to call repeatedly.

    Must run outside the event loop (it reads package metadata); calling it
    at import time of the integration satisfies that.
    """
    global _applied  # noqa: PLW0603
    if _applied:
        return
    _applied = True

    try:
        installed = version("gecko-iot-client")
    except PackageNotFoundError:
        _LOGGER.debug("gecko-iot-client not installed, client patches skipped")
        return

    if installed not in PATCHED_VERSIONS:
        _LOGGER.info(
            "gecko-iot-client %s is not in %s, client patches skipped",
            installed,
            sorted(PATCHED_VERSIONS),
        )
        return

    for name, patch in (
        ("#11 flow speed config", _patch_flow_speed_config),
        ("#12 set_color serialization", _patch_set_color),
        ("#13 set_mode_by_name spaces", _patch_set_mode_by_name),
    ):
        try:
            patch()
        except Exception:  # noqa: BLE001 - never break setup over a patch
            _LOGGER.exception("Could not apply gecko-iot-client patch %s", name)
        else:
            _LOGGER.debug("Applied gecko-iot-client patch %s", name)


# --- #11 ---------------------------------------------------------------------


def _is_range_config(value: dict) -> bool:
    return "minimum" in value and "maximum" in value


def _extract_value_from_config(field_value: Any) -> Any:
    """Keep min/max range dicts whole, unwrap other value wrappers."""
    if not isinstance(field_value, dict):
        return field_value
    if _is_range_config(field_value):
        return field_value
    for key in _SCALAR_VALUE_KEYS:
        if key in field_value:
            return field_value[key]
    return None


def _scalar_from_range(speed: dict) -> float | None:
    for key in _SCALAR_VALUE_KEYS:
        value = speed.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def _patch_flow_speed_config() -> None:
    from gecko_iot_client.models import zone_parser  # noqa: PLC0415
    from gecko_iot_client.models.flow_zone import FlowZone  # noqa: PLC0415

    zone_parser._extract_value_from_config = _extract_value_from_config  # noqa: SLF001

    original_init = FlowZone.__init__

    @functools.wraps(original_init)
    def __init__(self, zone_id: str, config: dict) -> None:  # noqa: N807
        speed_raw = config.get("speed")
        if not isinstance(speed_raw, dict):
            original_init(self, zone_id, config)
            return

        # Some range wrappers omit stepIncrement; FlowZone.capabilities
        # indexes it directly.
        speed_raw.setdefault("stepIncrement", 0)
        scalar = _scalar_from_range(speed_raw)

        # Let the original constructor see a scalar (it validates speed as a
        # number), then put the range back for speed_config/capabilities.
        config["speed"] = scalar
        try:
            original_init(self, zone_id, config)
        finally:
            config["speed"] = speed_raw
        self.config["speed"] = speed_raw
        self.speed = scalar

    FlowZone.__init__ = __init__


# --- #12 ---------------------------------------------------------------------


def _patch_set_color() -> None:
    from gecko_iot_client.models.lighting_zone import RGB, LightingZone  # noqa: PLC0415

    def set_color(self, r: int, g: int, b: int, i: int | None = None) -> None:
        """Set lighting color, publishing the device's [r, g, b, i] format."""
        if i is None:
            i = getattr(getattr(self, "rgbi", None), "i", None)
        rgb_color = RGB(r=r, g=g, b=b, i=i)
        self.rgbi = rgb_color
        self.active = True
        payload = [r, g, b] if i is None else [r, g, b, i]
        self._publish_desired_state({"rgbi": payload, "active": True})

    LightingZone.set_color = set_color


# --- #13 ---------------------------------------------------------------------


def _patch_set_mode_by_name() -> None:
    from gecko_iot_client.models.operation_mode_controller import (  # noqa: PLC0415
        OperationModeController,
    )

    original = OperationModeController.set_mode_by_name

    @functools.wraps(original)
    def set_mode_by_name(self, mode_name: str) -> None:
        return original(self, mode_name.strip().replace(" ", "_"))

    OperationModeController.set_mode_by_name = set_mode_by_name
