"""Tests for the gecko-iot-client runtime patches (client_patches.py)."""

from __future__ import annotations

from gecko_iot_client.models.flow_zone import FlowZone, FlowZoneCapabilities
from gecko_iot_client.models.lighting_zone import LightingZone
from gecko_iot_client.models.operation_mode import OperationMode
from gecko_iot_client.models.operation_mode_controller import OperationModeController
from gecko_iot_client.models.zone_parser import ZoneConfigurationParser
from gecko_iot_client.models.zone_types import ZoneType

from custom_components.gecko.client_patches import apply_client_patches

apply_client_patches()


def _flow_zone(speed_config: dict) -> FlowZone:
    zones = ZoneConfigurationParser().parse_zones_configuration(
        {"flow": {"1": {"pumps": ["1"], "speed": speed_config}}}
    )
    return zones[ZoneType.FLOW_ZONE][0]


def test_multi_speed_pump_keeps_range_and_exposes_presets() -> None:
    zone = _flow_zone({"minimum": 0, "maximum": 100, "stepIncrement": 50})

    assert zone.speed_config == {"minimum": 0, "maximum": 100, "stepIncrement": 50}
    assert FlowZoneCapabilities.SUPPORTS_SPEED_PRESETS in zone.capabilities
    assert zone.speed is None


def test_single_speed_pump_has_no_presets() -> None:
    zone = _flow_zone({"minimum": 100, "maximum": 100, "stepIncrement": 0})

    assert zone.speed_config is not None
    assert FlowZoneCapabilities.SUPPORTS_SPEED_PRESETS not in zone.capabilities


def test_range_without_step_increment_does_not_raise() -> None:
    zone = _flow_zone({"minimum": 0, "maximum": 100})

    assert FlowZoneCapabilities.SUPPORTS_SPEED_PRESETS not in zone.capabilities


def test_value_wrapper_still_becomes_scalar_speed() -> None:
    zone = FlowZone("1", {"speed": {"minimum": 0, "maximum": 100, "value": 40, "stepIncrement": 0}})

    assert zone.speed == 40.0


def test_set_color_publishes_a_json_serializable_list() -> None:
    zone = LightingZone("1", {})
    published: list[dict] = []
    zone._publish_desired_state = published.append  # noqa: SLF001

    zone.set_color(10, 20, 30, 1)

    assert published == [{"rgbi": [10, 20, 30, 1], "active": True}]
    assert zone.active is True


def test_set_mode_by_name_accepts_spaces() -> None:
    controller = OperationModeController()
    published: list[dict] = []
    controller._publish_desired_state = published.append  # noqa: SLF001

    controller.set_mode_by_name("Super Savings")

    assert published == [{"operationMode": OperationMode.SUPER_SAVINGS.value}]
