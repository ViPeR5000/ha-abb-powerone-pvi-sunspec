from homeassistant.const import (
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_VOLTAGE,
)

DOMAIN = "abb_sunspec_modbus"
DEFAULT_NAME = "abb_sunspec"
DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 2
DEFAULT_SCAN_INTERVAL = 30
MANUFACTURER = "ABB"
ATTR_STATUS_DESCRIPTION = "status_description"
ATTR_MANUFACTURER = "ABB"
CONF_ABB_SUNSPEC_HUB = "abb_sunspec_hub"
CONF_UNIT_ID = 2

SENSOR_TYPES = {
    "AC_Current": ["AC Current", "accurrent", "A", "mdi:current-ac", DEVICE_CLASS_CURRENT],
    "AC_CurrentA": ["AC Current A", "accurrenta", "A", "mdi:current-ac", DEVICE_CLASS_CURRENT],
    "AC_CurrentB": ["AC Current B", "accurrentb", "A", "mdi:current-ac", DEVICE_CLASS_CURRENT],
    "AC_CurrentC": ["AC Current C", "accurrentc", "A", "mdi:current-ac", DEVICE_CLASS_CURRENT],
    "AC_VoltageAB": ["AC Voltage AB", "acvoltageab", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "AC_VoltageBC": ["AC Voltage BC", "acvoltagebc", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "AC_VoltageCA": ["AC Voltage CA", "acvoltageca", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "AC_VoltageAN": ["AC Voltage AN", "acvoltagean", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "AC_VoltageBN": ["AC Voltage BN", "acvoltagebn", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "AC_VoltageCN": ["AC Voltage CN", "acvoltagecn", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "AC_Power": ["AC Power", "acpower", "W", "mdi:solar-power", DEVICE_CLASS_POWER],
    "AC_Frequency": ["AC Frequency", "acfreq", "Hz", "mdi:sine-wave", None],
    "AC_Energy_KWH": ["AC Energy KWH", "acenergy", "kWh", "mdi:solar-power", DEVICE_CLASS_ENERGY],
    "DC_Power": ["DC Power", "dcpower", "W", "mdi:solar-power", DEVICE_CLASS_POWER],
    "Temp_Cab": ["Temp. Cabinet", "tempcab", "°C", "mdi:temperature-celsius", DEVICE_CLASS_TEMPERATURE],
    "Temp_Oth": ["Temp. Booster", "tempoth", "°C", "mdi:temperature-celsius", DEVICE_CLASS_TEMPERATURE],
    "Status": ["Status", "status", None, "mdi:information-outline", None],
    "Status_Vendor": ["Status Vendor", "statusvendor", None, "mdi:information-outline", None],
    "DC1_Curr": ["DC1 total current", "dc1curr", "A", "mdi:current-ac", DEVICE_CLASS_CURRENT],
    "DC1_Volt": ["DC1 voltage", "dc1volt", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "DC1_Power": ["DC1 power", "dc1power", "W", "mdi:solar-power", DEVICE_CLASS_POWER],
    "DC2_Curr": ["DC2 total current", "dc2curr", "A", "mdi:current-ac", DEVICE_CLASS_CURRENT],
    "DC2_Volt": ["DC2 voltage", "dc2volt", "V", "mdi:lightning-bolt", DEVICE_CLASS_VOLTAGE],
    "DC2_Power": ["DC2 power", "dc2power", "W", "mdi:solar-power", DEVICE_CLASS_POWER],
}


DEVICE_STATUS = {
    1: "Off",
    2: "Sleeping (auto-shutdown) – Night mode",
    3: "Grid Monitoring/wake-up",
    4: "Inverter is ON and producing power",
    5: "Production (curtailed)",
    6: "Shutting down",
    7: "Fault",
    8: "Maintenance/setup",
}
