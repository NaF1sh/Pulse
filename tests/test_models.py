import pytest

from pulse.core.models import Kind, Notification


@pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), float("inf")])
def test_invalid_meter_values_are_rejected(value):
    with pytest.raises(ValueError, match="between 0 and 1"):
        Notification(1, "Audio", "Volume", kind=Kind.LEVEL, value=value)
