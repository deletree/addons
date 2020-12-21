import logging

import voluptuous as vol
from homeassistant.config import DATA_CUSTOMIZE
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.storage import Store
from homeassistant.util import sanitize_filename

from .core import utils
from .core.gateway1 import Gateway1
from .core.utils import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_DEVICES = 'devices'
CONF_DEBUG = 'debug'
CONF_BUZZER = 'buzzer'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_DEVICES): {
            cv.string: vol.Schema({
                vol.Optional('occupancy_timeout'): cv.positive_int,
            }, extra=vol.ALLOW_EXTRA),
        },
        vol.Optional(CONF_BUZZER): cv.boolean,
        vol.Optional(CONF_DEBUG): cv.string,
    }, extra=vol.ALLOW_EXTRA),
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, hass_config: dict):
    config = hass_config.get(DOMAIN) or {}

    config.setdefault('devices', {})

    if 'debug' in config:
        debug = utils.RS485Gateway1Debug(hass)
        _LOGGER.setLevel(logging.DEBUG)
        _LOGGER.addHandler(debug)

    hass.data[DOMAIN] = {'config': config}

    await _handle_device_remove(hass)

    # utils.migrate_unique_id(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry):
    """Support one kind of enties -Gateway."""

    config = hass.data[DOMAIN]['config']

    hass.data[DOMAIN][config_entry.entry_id] = \
        gw = Gateway1(**config_entry.data, config=config)

    # init setup for each supported domains
    for domain in (
            'binary_sensor', 'climate', 'cover', 'light', 'remote', 'sensor',
            'switch'
    ):
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(
            config_entry, domain))

    gw.start()

    return True


# async def async_unload_entry(hass: HomeAssistant, config_entry):
#     return True

async def _handle_device_remove(hass: HomeAssistant):
    """Remove device from Hass if the device is renamed to
    `delete`.
    """

    async def device_registry_updated(event: Event):
        if event.data['action'] != 'update':
            return

        registry = hass.data['device_registry']
        hass_device = registry.async_get(event.data['device_id'])

        # check empty identifiers
        if not hass_device or not hass_device.identifiers:
            return

        domain, mac = next(iter(hass_device.identifiers))
        # handle only our devices
        if domain != DOMAIN or hass_device.name_by_user != 'delete':
            return

         # remove from Hass
        registry.async_remove_device(hass_device.id)

    hass.bus.async_listen('device_registry_updated', device_registry_updated)


class Gateway1Device(Entity):
    _ignore_offline = None
    _state = None

    def __init__(self, gateway: Gateway1, device: dict, attr: str):
        self.gw = gateway
        self.device = device

        self._attr = attr
        self._attrs = {}

        self._unique_id = f"{self.device['mac']}_{self._attr}"
        self._name = (self.device['device_name'] + ' ' +
                      self._attr.replace('_', ' ').title())

        self.entity_id = f"{DOMAIN}.{self._unique_id}"

    def debug(self, message: str):
        _LOGGER.debug(f"{self.entity_id} | {message}")

    async def async_added_to_hass(self):
        """Also run when rename entity_id"""
        custom: dict = self.hass.data[DATA_CUSTOMIZE].get(self.entity_id)
        self._ignore_offline = custom.get('ignore_offline')

        if 'init' in self.device and self._state is None:
            self.update(self.device['init'])

        self.gw.add_update(self.device['did'], self.update)

    async def async_will_remove_from_hass(self) -> None:
        """Also run when rename entity_id"""
        self.gw.remove_update(self.device['did'], self.update)

    # @property
    # def entity_registry_enabled_default(self):
    #     return False

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def available(self) -> bool:
        return self.device.get('online', True) or self._ignore_offline

    @property
    def device_state_attributes(self):
        return self._attrs

    @property
    def device_info(self):
        """
        https://developers.home-assistant.io/docs/device_registry_index/
        """
        type_ = self.device['type']
        if type_ == 'gateway':
            return {
                'identifiers': {(DOMAIN, self.device['mac'])},
                'manufacturer': self.device['device_manufacturer'],
                'model': self.device['device_model'],
                'name': self.device['device_name']
            }
        elif type_ == 'zigbee':
            return {
                'connections': {(type_, self.device['mac'])},
                'identifiers': {(DOMAIN, self.device['mac'])},
                'manufacturer': self.device['device_manufacturer'],
                'model': self.device['device_model'],
                'name': self.device['device_name'],
                'sw_version': self.device['zb_ver'],
                'via_device': (DOMAIN, self.gw.device['mac'])
            }

    def update(self, data: dict):
        pass
