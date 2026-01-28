"""Sensor platform for Cat Care Tracker."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
    CONF_CAT_NAME,
    CHECKIN_TYPE_FOOD,
    CHECKIN_TYPE_INSULIN,
    CHECKIN_TYPE_WATER,
    CHECKIN_TYPE_BG,
    COL_DATE,
    COL_CHECKIN_TYPE,
    COL_WATER_REFILL,
    COL_BG_LEVEL,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Cat Care Tracker sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    cat_name = entry.data.get(CONF_CAT_NAME, "My Cat")

    sensors = [
        LastCheckInSensor(coordinator, entry, cat_name, CHECKIN_TYPE_FOOD, "last_feeding", "Last Feeding"),
        LastCheckInSensor(coordinator, entry, cat_name, CHECKIN_TYPE_INSULIN, "last_insulin", "Last Insulin"),
        LastCheckInSensor(coordinator, entry, cat_name, CHECKIN_TYPE_WATER, "last_water", "Last Water"),
        LastCheckInSensor(coordinator, entry, cat_name, CHECKIN_TYPE_BG, "last_bg", "Last Blood Glucose"),
        DailyCountSensor(coordinator, entry, cat_name, CHECKIN_TYPE_FOOD, "daily_feedings", "Daily Feedings"),
        DailyCountSensor(coordinator, entry, cat_name, CHECKIN_TYPE_INSULIN, "daily_insulin", "Daily Insulin"),
        TodayEntriesSensor(coordinator, entry, cat_name),
    ]

    async_add_entities(sensors)


class CatCareTrackerSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Cat Care Tracker sensors."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        cat_name: str,
        sensor_id: str,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._cat_name = cat_name
        self._attr_unique_id = f"{entry.entry_id}_{sensor_id}"
        self._attr_name = f"{cat_name} {name}"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"{self._cat_name} Care Tracker",
            "manufacturer": "Cat Care Tracker",
            "model": "Google Sheets Integration",
        }


class LastCheckInSensor(CatCareTrackerSensorBase):
    """Sensor for last check-in of a specific type."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        cat_name: str,
        checkin_type: str,
        sensor_id: str,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, cat_name, sensor_id, name)
        self._checkin_type = checkin_type
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        last_entry = self.coordinator.data.get(f"last_{self._checkin_type}")
        if not last_entry:
            return None

        date_str = last_entry.get(COL_DATE, "")
        if not date_str:
            return None

        try:
            # Try parsing with time
            return datetime.strptime(date_str, "%m/%d/%Y %H:%M")
        except ValueError:
            try:
                # Try parsing without time
                return datetime.strptime(date_str, "%m/%d/%Y")
            except ValueError:
                return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}

        last_entry = self.coordinator.data.get(f"last_{self._checkin_type}")
        if not last_entry:
            return {}

        attrs = {
            "checkin_types": last_entry.get(COL_CHECKIN_TYPE, ""),
        }

        # Add specific attributes based on type
        if self._checkin_type == CHECKIN_TYPE_WATER:
            attrs["water_refill"] = last_entry.get(COL_WATER_REFILL, "")
        elif self._checkin_type == CHECKIN_TYPE_BG:
            attrs["bg_level"] = last_entry.get(COL_BG_LEVEL, "")

        return attrs


class DailyCountSensor(CatCareTrackerSensorBase):
    """Sensor for daily count of a specific check-in type."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        cat_name: str,
        checkin_type: str,
        sensor_id: str,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, cat_name, sensor_id, name)
        self._checkin_type = checkin_type
        self._attr_icon = "mdi:counter"

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return 0

        counts = self.coordinator.data.get("today_counts", {})
        return counts.get(self._checkin_type, 0)


class TodayEntriesSensor(CatCareTrackerSensorBase):
    """Sensor that shows all of today's entries."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        cat_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, cat_name, "today_entries", "Today's Entries")
        self._attr_icon = "mdi:clipboard-list"

    @property
    def native_value(self) -> int:
        """Return the count of today's entries."""
        if not self.coordinator.data:
            return 0

        entries = self.coordinator.data.get("today_entries", [])
        return len(entries)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes with entry details."""
        if not self.coordinator.data:
            return {"entries": []}

        entries = self.coordinator.data.get("today_entries", [])
        return {
            "entries": entries,
            "food_count": self.coordinator.data.get("today_counts", {}).get(CHECKIN_TYPE_FOOD, 0),
            "insulin_count": self.coordinator.data.get("today_counts", {}).get(CHECKIN_TYPE_INSULIN, 0),
            "water_count": self.coordinator.data.get("today_counts", {}).get(CHECKIN_TYPE_WATER, 0),
            "bg_count": self.coordinator.data.get("today_counts", {}).get(CHECKIN_TYPE_BG, 0),
        }
