"""A pump zone that reports active without a speed.

GeckoFan only set `_attr_speed` from a numeric speed or when the zone was
inactive, and `_handle_coordinator_update` logs `self._attr_speed` before
anything else. A zone that is active with no speed therefore raised
AttributeError on every coordinator update, and the entity's state was never
written again.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from gecko_iot_client.models.zone_types import ZoneType

from custom_components.gecko.const import DOMAIN
from custom_components.gecko.coordinator import GeckoVesselCoordinator
from custom_components.gecko.fan import GeckoFan

from .conftest import MONITOR_ID, build_zones


async def test_active_pump_without_speed_updates(hass, network):
    entry = MockConfigEntry(domain=DOMAIN, entry_id="entry-1", data={})
    entry.add_to_hass(hass)
    entry.runtime_data = SimpleNamespace(api_client=None, coordinators=[])
    coordinator = GeckoVesselCoordinator(hass, entry.entry_id, "vessel-1", MONITOR_ID, "Spa")
    network.next_zones_on_connect = build_zones({"flow": {"1": {"active": True}}})
    assert await coordinator.async_setup_monitor_connection("wss://first")
    await hass.async_block_till_done()
    zone = next(z for z in coordinator.get_zones_by_type(ZoneType.FLOW_ZONE) if z.id == "1")
    assert zone.active is True and zone.speed is None, "the fixture must be active without a speed"

    fan = GeckoFan(coordinator, entry, zone)
    with patch.object(fan, "async_write_ha_state") as write:
        fan._handle_coordinator_update()

    write.assert_called_once()
    assert fan.is_on is True


async def test_pump_running_for_filtration_shows_on_but_refuses_turn_off(hass, network):
    """The fan reflects the physical pump; automatic demand blocks turn-off."""
    entry = MockConfigEntry(domain=DOMAIN, entry_id="entry-1", data={})
    entry.add_to_hass(hass)
    entry.runtime_data = SimpleNamespace(api_client=None, coordinators=[])
    coordinator = GeckoVesselCoordinator(hass, entry.entry_id, "vessel-1", MONITOR_ID, "Spa")
    network.next_zones_on_connect = build_zones(
        {"flow": {"1": {"active": True, "speed": 100, "initiators_": ["FILTRATION"]}}}
    )
    assert await coordinator.async_setup_monitor_connection("wss://first")
    await hass.async_block_till_done()
    zone = next(z for z in coordinator.get_zones_by_type(ZoneType.FLOW_ZONE) if z.id == "1")

    fan = GeckoFan(coordinator, entry, zone)
    with patch.object(fan, "async_write_ha_state"):
        fan._handle_coordinator_update()

    assert fan.is_on is True
    assert fan.extra_state_attributes["user_controlled"] is False

    with patch.object(zone, "deactivate") as deactivate:
        await fan.async_turn_off()
    deactivate.assert_not_called()


def _single_speed_zones(active: bool):
    from gecko_iot_client.models.zone_parser import ZoneConfigurationParser

    from custom_components.gecko.client_patches import apply_client_patches

    apply_client_patches()
    parser = ZoneConfigurationParser()
    zones = parser.parse_zones_configuration(
        {
            "flow": {
                "1": {
                    "name": "Pump 1",
                    "pumps": ["1"],
                    "speed": {"minimum": 100, "maximum": 100, "stepIncrement": 0},
                }
            }
        }
    )
    parser.apply_state_to_zones(
        zones,
        {"state": {"reported": {"zones": {"flow": {"1": {"active": active, "speed": 100}}}}}},
    )
    return zones


async def test_single_speed_pump_only_switches_on_and_off(hass, network):
    """A pump configured with minimum == maximum speed offers no speed control."""
    from homeassistant.components.fan import FanEntityFeature

    from custom_components.gecko.telemetry import (
        derive_flow_speed_mode,
        get_supported_flow_speed_modes,
    )

    entry = MockConfigEntry(domain=DOMAIN, entry_id="entry-1", data={})
    entry.add_to_hass(hass)
    entry.runtime_data = SimpleNamespace(api_client=None, coordinators=[])
    coordinator = GeckoVesselCoordinator(hass, entry.entry_id, "vessel-1", MONITOR_ID, "Spa")
    network.next_zones_on_connect = _single_speed_zones(active=True)
    assert await coordinator.async_setup_monitor_connection("wss://first")
    await hass.async_block_till_done()
    zone = next(z for z in coordinator.get_zones_by_type(ZoneType.FLOW_ZONE) if z.id == "1")

    assert get_supported_flow_speed_modes(zone) == ()
    assert derive_flow_speed_mode(zone) == "on"

    fan = GeckoFan(coordinator, entry, zone)
    fan.hass = hass
    assert not fan.supported_features & FanEntityFeature.SET_SPEED
    assert fan.is_on is True

    published: list = []
    zone.set_publish_callback(lambda *args: published.append(args[-1]))
    await fan.async_turn_on()
    assert published == [{"active": True}]
