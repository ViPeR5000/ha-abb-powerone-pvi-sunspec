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
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_UNIT_ID,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_STATUS,
    CONF_UNIT_ID,
)

_LOGGER = logging.getLogger(__name__)

ABB_SUNSPEC_MODBUS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.positive_int,
        #vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): cv.positive_int,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
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
    #unit_id = entry.data[CONF_UNIT_ID]
    scan_interval = entry.data[CONF_SCAN_INTERVAL]

    _LOGGER.debug("Setup %s.%s", DOMAIN, name)

    hub = ABBSunSpecModbusHub(
        # hass, name, host, port, unit_id, scan_interval
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
        # unit_id,
        scan_interval,
    ):
        """Initialize the Modbus hub."""
        self._hass = hass
        self._client = ModbusTcpClient(host=host, port=port)
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

    def calculate_value(self, value, sf):
        return value * 10 ** sf

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
        self.data["acenergy"] = 1
        self.data["dcpower"] = 1
        self.data["tempcab"] = 1
        self.data["mppt1curr"] = 1
        self.data["status"] = 1
        self.data["statusvendor"] = 1
        self.data["mppt1curr"] = 1
        self.data["mppt1volt"] = 1
        self.data["mppt1power"] = 1
        self.data["mppt2curr"] = 1
        self.data["mppt2volt"] = 1
        self.data["mppt2power"] = 1
        return True


    def read_modbus_data_inverter(self):
        inverter_data = self.read_holding_registers(unit=2, address=72, count=184)
        if not inverter_data.isError():
            decoder = BinaryPayloadDecoder.fromRegisters(
                inverter_data.registers, byteorder=Endian.Big
            )

            # registers 72 to 76
            accurrent = decoder.decode_16bit_uint()
            accurrenta = decoder.decode_16bit_uint()
            accurrentb = decoder.decode_16bit_uint()
            accurrentc = decoder.decode_16bit_uint()
            accurrentsf = decoder.decode_16bit_int()
            accurrent = self.calculate_value(accurrent, accurrentsf)
            accurrenta = self.calculate_value(accurrenta, accurrentsf)
            accurrentb = self.calculate_value(accurrentb, accurrentsf)
            accurrentc = self.calculate_value(accurrentc, accurrentsf)
            self.data["accurrent"] = round(accurrent, abs(accurrentsf))
            self.data["accurrenta"] = round(accurrenta, abs(accurrentsf))
            self.data["accurrentb"] = round(accurrentb, abs(accurrentsf))
            self.data["accurrentc"] = round(accurrentc, abs(accurrentsf))


            # registers 77 to 83
            acvoltageab = decoder.decode_16bit_uint()
            acvoltagebc = decoder.decode_16bit_uint()
            acvoltageca = decoder.decode_16bit_uint()
            acvoltagean = decoder.decode_16bit_uint()
            acvoltagebn = decoder.decode_16bit_uint()
            acvoltagecn = decoder.decode_16bit_uint()
            acvoltagesf = decoder.decode_16bit_int()
            acvoltageab = self.calculate_value(acvoltageab, acvoltagesf)
            acvoltagebc = self.calculate_value(acvoltagebc, acvoltagesf)
            acvoltageca = self.calculate_value(acvoltageca, acvoltagesf)
            acvoltagean = self.calculate_value(acvoltagean, acvoltagesf)
            acvoltagebn = self.calculate_value(acvoltagebn, acvoltagesf)
            acvoltagecn = self.calculate_value(acvoltagecn, acvoltagesf)
            self.data["acvoltageab"] = round(acvoltageab, abs(acvoltagesf))
            self.data["acvoltagebc"] = round(acvoltagebc, abs(acvoltagesf))
            self.data["acvoltageca"] = round(acvoltageca, abs(acvoltagesf))
            self.data["acvoltagean"] = round(acvoltagean, abs(acvoltagesf))
            self.data["acvoltagebn"] = round(acvoltagebn, abs(acvoltagesf))
            self.data["acvoltagecn"] = round(acvoltagecn, abs(acvoltagesf))

            # registers 84 to 85
            acpower = decoder.decode_16bit_int()
            acpowersf = decoder.decode_16bit_int()
            acpower = self.calculate_value(acpower, acpowersf)
            self.data["acpower"] = round(acpower, abs(acpowersf))

            # registers 86 to 87
            acfreq = decoder.decode_16bit_uint()
            acfreqsf = decoder.decode_16bit_int()
            acfreq = self.calculate_value(acfreq, acfreqsf)
            self.data["acfreq"] = round(acfreq, abs(acfreqsf))

            # skip register 88-93
            decoder.skip_bytes(12)

             # registers 94 to 96
            acenergy = decoder.decode_32bit_uint()
            acenergysf = decoder.decode_16bit_uint()
            acenergy = self.calculate_value(acenergy, acenergysf)
            self.data["acenergy"] = round(acenergy * 0.001, 3)

            # skip register 97 to 100
            decoder.skip_bytes(8)

             # registers 101 to 102
            dcpower = decoder.decode_16bit_int()
            dcpowersf = decoder.decode_16bit_int()
            dcpower = self.calculate_value(dcpower, dcpowersf)
            self.data["dcpower"] = round(dcpower, abs(dcpowersf))

             # register 103
            tempcab = decoder.decode_16bit_int()
            # skip registers 104-105
            decoder.skip_bytes(4)
            # register 106 to 107
            mppt1curr = decoder.decode_16bit_int()
            tempsf = decoder.decode_16bit_int()
            #tempcab = self.calculate_value(tempcab, tempsf)
            #self.data["tempcab"] = round(tempcab, abs(tempsf))
            mppt1curr = self.calculate_value(mppt1curr, tempsf)
            self.data["mppt1curr"] = round(mppt1curr, abs(tempsf))

            # register 108
            status = decoder.decode_16bit_int()
            self.data["status"] = status

            # register 109
            statusvendor = decoder.decode_16bit_int()
            self.data["statusvendor"] = statusvendor

            # skip register 110 to 124
            decoder.skip_bytes(30)

            # registers 125 to 127
            dcasf = decoder.decode_16bit_int()
            dcvsf = decoder.decode_16bit_int()
            dcwsf = decoder.decode_16bit_int()

            # skip register 128 to 133
            decoder.skip_bytes(26)

            # registers 141 to 143
            mppt1curr = decoder.decode_16bit_uint()
            mppt1volt = decoder.decode_16bit_uint()
            mppt1power = decoder.decode_16bit_uint()
            mppt1curr = self.calculate_value(mppt1curr, dcasf)
            self.data["mppt1curr"] = round(mppt1curr, abs(dcasf))
            mppt1volt = self.calculate_value(mppt1volt, dcvsf)
            self.data["mppt1volt"] = round(mppt1volt, abs(dcvsf))
            mppt1power = self.calculate_value(mppt1power, dcwsf)
            self.data["mppt1power"] = round(mppt1power, abs(dcwsf))

            # skip register 144 to 160
            decoder.skip_bytes(34)

            # registers 161 to 163
            mppt2curr = decoder.decode_16bit_uint()
            mppt2volt = decoder.decode_16bit_uint()
            mppt2power = decoder.decode_16bit_uint()
            mppt2curr = self.calculate_value(mppt2curr, dcasf)
            self.data["mppt2curr"] = round(mppt2curr, abs(dcasf))
            mppt2volt = self.calculate_value(mppt2volt, dcvsf)
            self.data["mppt2volt"] = round(mppt2volt, abs(dcvsf))
            mppt2power = self.calculate_value(mppt2power, dcwsf)
            self.data["mppt2power"] = round(mppt2power, abs(dcwsf))

            return True
        else:
            return False
