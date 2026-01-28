"""Tests for Cat Care Tracker constants."""
from custom_components.cat_care_tracker.const import (
    DOMAIN,
    CONF_SPREADSHEET_ID,
    CONF_CAT_NAME,
    CHECKIN_TYPE_FOOD,
    CHECKIN_TYPE_WATER,
    CHECKIN_TYPE_INSULIN,
    CHECKIN_TYPE_BG,
    CHECKIN_TYPES,
    COL_TIMESTAMP,
    COL_DATE,
    COL_CHECKIN_TYPE,
    COL_WATER_REFILL,
    COL_BG_LEVEL,
    SERVICE_LOG_ENTRY,
    SERVICE_LOG_FEEDING,
    SERVICE_LOG_INSULIN,
    SERVICE_LOG_WATER,
    SERVICE_LOG_BLOOD_GLUCOSE,
    DEFAULT_UPDATE_INTERVAL,
)


def test_domain():
    """Test domain constant."""
    assert DOMAIN == "cat_care_tracker"


def test_config_keys():
    """Test configuration key constants."""
    assert CONF_SPREADSHEET_ID == "spreadsheet_id"
    assert CONF_CAT_NAME == "cat_name"


def test_checkin_types():
    """Test check-in type constants."""
    assert CHECKIN_TYPE_FOOD == "Food"
    assert CHECKIN_TYPE_WATER == "Water"
    assert CHECKIN_TYPE_INSULIN == "Insulin"
    assert CHECKIN_TYPE_BG == "Blood Glucose Measurement"

    # All types should be in the list
    assert CHECKIN_TYPE_FOOD in CHECKIN_TYPES
    assert CHECKIN_TYPE_WATER in CHECKIN_TYPES
    assert CHECKIN_TYPE_INSULIN in CHECKIN_TYPES
    assert CHECKIN_TYPE_BG in CHECKIN_TYPES
    assert len(CHECKIN_TYPES) == 4


def test_column_names():
    """Test column name constants."""
    assert COL_TIMESTAMP == "Timestamp"
    assert COL_DATE == "Date"
    assert COL_CHECKIN_TYPE == "Checkin Type"
    assert COL_WATER_REFILL == "Water Refill"
    assert COL_BG_LEVEL == "BG (mg/dL)"


def test_service_names():
    """Test service name constants."""
    assert SERVICE_LOG_ENTRY == "log_entry"
    assert SERVICE_LOG_FEEDING == "log_feeding"
    assert SERVICE_LOG_INSULIN == "log_insulin"
    assert SERVICE_LOG_WATER == "log_water"
    assert SERVICE_LOG_BLOOD_GLUCOSE == "log_blood_glucose"


def test_default_update_interval():
    """Test default update interval is reasonable."""
    # Should be at least 5 minutes (300 seconds) to avoid API rate limits
    assert DEFAULT_UPDATE_INTERVAL >= 300
    # Should be at most 30 minutes (1800 seconds) for reasonable responsiveness
    assert DEFAULT_UPDATE_INTERVAL <= 1800
