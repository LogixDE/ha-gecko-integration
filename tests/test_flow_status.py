"""The flow status sensor translates the shadow's short codes."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from custom_components.gecko.sensor import GeckoTemperatureFlowStatusSensor


@pytest.mark.parametrize(
    ("raw", "state"),
    [("OK", "ok"), ("IP", "flow_check"), ("XY", "other"), (None, None)],
)
def test_flow_status_codes(raw, state) -> None:
    sensor = object.__new__(GeckoTemperatureFlowStatusSensor)
    sensor._zone = SimpleNamespace(id="1")
    sensor.coordinator = SimpleNamespace(get_spa_state=lambda: {})

    with patch(
        "custom_components.gecko.sensor.get_temperature_flow_status", return_value=raw
    ):
        sensor._update_from_coordinator()

    assert sensor.native_value == state
    assert sensor.extra_state_attributes["raw_code"] == raw
    assert state is None or state in sensor.options
