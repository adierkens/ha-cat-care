"""Constants for Cat Care Tracker integration."""

DOMAIN = "cat_care_tracker"

# Configuration keys
CONF_SPREADSHEET_ID = "spreadsheet_id"
CONF_CREDENTIALS_FILE = "credentials_file"
CONF_CAT_NAME = "cat_name"
CONF_SHEET_NAME = "sheet_name"

# Check-in types (matching Google Form options)
CHECKIN_TYPE_FOOD = "Food"
CHECKIN_TYPE_WATER = "Water"
CHECKIN_TYPE_INSULIN = "Insulin"
CHECKIN_TYPE_BG = "Blood Glucose Measurement"

CHECKIN_TYPES = [
    CHECKIN_TYPE_FOOD,
    CHECKIN_TYPE_WATER,
    CHECKIN_TYPE_INSULIN,
    CHECKIN_TYPE_BG,
]

# Sheet column names
COL_TIMESTAMP = "Timestamp"
COL_DATE = "Date"
COL_CHECKIN_TYPE = "Checkin Type"
COL_WATER_REFILL = "Water Refill"
COL_BG_LEVEL = "BG (mg/dL)"

# Services
SERVICE_LOG_ENTRY = "log_entry"
SERVICE_LOG_FEEDING = "log_feeding"
SERVICE_LOG_INSULIN = "log_insulin"
SERVICE_LOG_WATER = "log_water"
SERVICE_LOG_BLOOD_GLUCOSE = "log_blood_glucose"

# Sensors
SENSOR_LAST_FEEDING = "last_feeding"
SENSOR_LAST_INSULIN = "last_insulin"
SENSOR_LAST_WATER = "last_water"
SENSOR_LAST_BG = "last_blood_glucose"
SENSOR_DAILY_FEEDINGS = "daily_feedings"
SENSOR_DAILY_INSULIN = "daily_insulin"

# Attributes
ATTR_TIMESTAMP = "timestamp"
ATTR_CHECKIN_TYPES = "checkin_types"
ATTR_WATER_REFILL = "water_refill"
ATTR_BG_LEVEL = "bg_level"
ATTR_ENTRIES_TODAY = "entries_today"

# Default values
DEFAULT_UPDATE_INTERVAL = 600  # 10 minutes in seconds (conservative for API rate limits)
