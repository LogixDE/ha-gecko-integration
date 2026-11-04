"""The thermostat offers the watercare mode as preset mode."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.climate import ClimateEntityFeature
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from gecko_iot_client.models.operation_mode import OperationMode
from gecko_iot_client.models.operation_mode_controller import OperationModeController
from gecko_iot_client.models.zone_types import ZoneType

from custom_components.gecko.client_patches import apply_client_patches
from custom_components.gecko.climate import GeckoClimate
from custom_components.gecko.const import DOMAIN
from custom_components.gecko.coordinator import GeckoVesselCoordinator

from .conftest import MONITOR_ID, build_zones

apply_client_patches()


async def _thermostat(hass, network):
    entry = MockConfigEntry(domain=DOMAIN, entry_id="entry-1", data={})
    entry.add_to_hass(hass)
    entry.runtime_data = SimpleNamespace(api_client=None, coordinators=[])
    coordinator = GeckoVesselCoordinator(hass, entry.entry_id, "vessel-1", MONITOR_ID, "Spa")
    network.next_zones_on_connect = build_zones()
    assert await coordinator.async_setup_monitor_connection("wss://first")
    await hass.async_block_till_done()
    zone = coordinator.get_zones_by_type(ZoneType.TEMPERATURE_CONTROL_ZONE)[0]
    climate = GeckoClimate(coordinator, zone)
    climate.hass = hass

    controller = OperationModeController()
    controller.operation_mode = OperationMode.AWAY
    published: list[dict] = []
    controller.set_publish_callback(lambda _feature, updates: published.append(updates))
    client = SimpleNamespace(operation_mode_controller=controller)
    return climate, coordinator, client, published


async def test_thermostat_reports_watercare_mode_as_preset(hass, network):
    climate, _coordinator, client, _published = await _thermostat(hass, network)

    with patch.object(climate, "_get_gecko_client_sync", return_value=client):
        assert climate.supported_features & ClimateEntityFeature.PRESET_MODE
        assert climate.preset_modes == ["Away", "Standard", "Savings", "Super Savings", "Weekender"]
        assert climate.preset_mode == "Away"


async def test_thermostat_sets_watercare_mode(hass, network):
    climate, coordinator, client, published = await _thermostat(hass, network)

    with (
        patch.object(coordinator, "get_gecko_client", AsyncMock(return_value=client)),
        patch.object(coordinator, "async_request_refresh", AsyncMock()),
    ):
        await climate.async_set_preset_mode("Super Savings")

    assert published == [{"operationMode": OperationMode.SUPER_SAVINGS.value}]


async def test_thermostat_rejects_unknown_preset(hass, network):
    climate, _coordinator, _client, _published = await _thermostat(hass, network)

    with pytest.raises(ServiceValidationError):
        await climate.async_set_preset_mode("Other")
