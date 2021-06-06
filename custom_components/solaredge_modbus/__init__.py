"""The ABB SunSpec Modbus Integration."""
import asyncio
import logging
import threading
from datetime import timedelta
from typing import Optional

import voluptuous as vol
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, CONF_UNITID
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval
from .const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

ABB_SUNSPEC_MODBUS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.string,
        vol.Required(CONF_UNITID): cv.string,
        vol.Optional(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
        ): cv.positive_int,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({cv.slug: ABB_SUNSPEC_MODBUS_SCHEMA})}, extra=vol.ALLOW_EXTRA
)

PLATFORMS = ["sensor"]


async def async_setup(hass, config):
    """Set up ABB Sunspec Modbus component"""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up ABB Sunspec Modbus"""
    host = entry.data[CONF_HOST]
    name = entry.data[CONF_NAME]
    port = entry.data[CONF_PORT]
    unitid = entry.data[CONF_UNITID]
    scan_interval = entry.data[CONF_SCAN_INTERVAL]

    _LOGGER.debug("Setup %s.%s", DOMAIN, name)

    hub = ABBSunSpecModbusHub(
        hass, name, host, port, scan_interval
    )
    """Register the hub."""
    hass.data[DOMAIN][name] = {"hub": hub}

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )
    return True


async def async_unload_entry(hass, entry):
    """Unload ABB SunSpec Modbus entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if not unload_ok:
        return False

    hass.data[DOMAIN].pop(entry.data["name"])
    return True


class ABBSunSpecModbusHub:
    """Thread safe wrapper class for pymodbus."""

    def __init__(
        self,
        hass,
        name,
        host,
        port,
        unitid,
        scan_interval,
    ):
        """Initialize the Modbus hub."""
        self._hass = hass
        self._client = ModbusTcpClient(host=host, port=port, unit_id=unitid)
        self._lock = threading.Lock()
        self._name = name
        self._scan_interval = timedelta(seconds=scan_interval)
        self._unsub_interval_method = None
        self._sensors = []
        self.data = {}

    @callback
    def async_add_abb_sunspec_sensor(self, update_callback):
        """Listen for data updates."""
        # This is the first sensor, set up interval.
        if not self._sensors:
            self.connect()
            self._unsub_interval_method = async_track_time_interval(
                self._hass, self.async_refresh_modbus_data, self._scan_interval
            )

        self._sensors.append(update_callback)

    @callback
    def async_remove_abb_sunspec_sensor(self, update_callback):
        """Remove data update."""
        self._sensors.remove(update_callback)

        if not self._sensors:
            """stop the interval timer upon removal of last sensor"""
            self._unsub_interval_method()
            self._unsub_interval_method = None
            self.close()

    async def async_refresh_modbus_data(self, _now: Optional[int] = None) -> None:
        """Time to update."""
        if not self._sensors:
            return

        update_result = self.read_modbus_data()

        if update_result:
            for update_callback in self._sensors:
                update_callback()

    @property
    def name(self):
        """Return the name of this hub."""
        return self._name

    def close(self):
        """Disconnect client."""
        with self._lock:
            self._client.close()

    def connect(self):
        """Connect client."""
        with self._lock:
            self._client.connect()

    def read_holding_registers(self, unit, address, count):
        """Read holding registers."""
        with self._lock:
            kwargs = {"unit": unit} if unit else {}
            return self._client.read_holding_registers(address, count, **kwargs)

    def read_modbus_data_stub(self):
        return (
            self.read_modbus_data_inverter_stub()
        )

    def read_modbus_data(self):
        return (
            self.read_modbus_data_inverter()
        )

    def read_modbus_data_inverter_stub(self):
        self.data["accurrent"] = 1
        self.data["accurrenta"] = 1
        self.data["accurrentb"] = 1
        self.data["accurrentc"] = 1
        self.data["acvoltageab"] = 1
        self.data["acvoltagebc"] = 1
        self.data["acvoltageca"] = 1
        self.data["acvoltagean"] = 1
        self.data["acvoltagebn"] = 1
        self.data["acvoltagecn"] = 1
        self.data["acpower"] = 1
        self.data["acfreq"] = 1
        self.data["acva"] = 1
        self.data["acvar"] = 1
        self.data["acpf"] = 1
        self.data["acenergy"] = 1
        self.data["dccurrent"] = 1
        self.data["dcvoltage"] = 1
        self.data["dcpower"] = 1
        self.data["tempsink"] = 1
        self.data["status"] = 1
        self.data["statusvendor"] = 1

        return True


    def read_modbus_data_inverter(self):
        inverter_data = self.read_holding_registers(address=72, count=38)
        if not inverter_data.isError():
            decoder = BinaryPayloadDecoder.fromRegisters(
                inverter_data.registers, byteorder=Endian.Big
            )

            # registers 72 to 75
            accurrent = decoder.decode_16bit_uint()
            accurrenta = decoder.decode_16bit_uint()
            accurrentb = decoder.decode_16bit_uint()
            accurrentc = decoder.decode_16bit_uint()

            # skip register 76
            decoder.skip_bytes(2)

            # registers 77 to 82
            acvoltageab = decoder.decode_16bit_uint()
            acvoltagebc = decoder.decode_16bit_uint()
            acvoltageca = decoder.decode_16bit_uint()
            acvoltagean = decoder.decode_16bit_uint()
            acvoltagebn = decoder.decode_16bit_uint()
            acvoltagecn = decoder.decode_16bit_uint()

            # skip register 83
            decoder.skip_bytes(2)

            # register 84
            acpower = decoder.decode_16bit_int()

            # skip register 85
            decoder.skip_bytes(2)

            # register 86
            acfreq = decoder.decode_16bit_uint()

            # skip register 87
            decoder.skip_bytes(2)

            # register 88
            acva = decoder.decode_16bit_int()

            # skip register 89
            decoder.skip_bytes(2)

            # register 90
            acvar = decoder.decode_16bit_int()

            # skip register 91
            decoder.skip_bytes(2)

            # register 92
            acpf = decoder.decode_16bit_int()

            # skip register 93
            decoder.skip_bytes(2)

            # register 94
            acenergy = decoder.decode_32bit_uint()
            self.data["acenergy"] = round(acenergy * 0.001, 3)

            # skip register 96
            decoder.skip_bytes(2)

            # register 97 (103)
            dccurrent = decoder.decode_16bit_uint()
  
            # skip register 98
            decoder.skip_bytes(2)

            # register 99 (103)
            dcvoltage = decoder.decode_16bit_uint()

            # skip register 100
            decoder.skip_bytes(2)

            # register 101
            dcpower = decoder.decode_16bit_int()

            # skip register 102-103
            decoder.skip_bytes(4)

            tempsink = decoder.decode_16bit_int()

            # skip 3 registers
            decoder.skip_bytes(6)

            status = decoder.decode_16bit_int()
            self.data["status"] = status
            statusvendor = decoder.decode_16bit_int()
            self.data["statusvendor"] = statusvendor

            return True
        else:
            return False
