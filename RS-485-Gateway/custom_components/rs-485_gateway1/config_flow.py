import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from . import DOMAIN
from .core import gateway1

_LOGGER = logging.getLogger(__name__)

ACTIONS = {
    'token': "Add Gateway using Token"
}

SERVERS = {
    'cn': "China",
}


class RS485Gateway1FlowHandler(ConfigFlow, domain=DOMAIN):
 
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            if user_input['action'] == 'cloud':
                return await self.async_step_cloud()
            elif user_input['action'] == 'token':
                return await self.async_step_token()
            else:
                device = next(d for d in self.hass.data[DOMAIN]['devices']
                              if d['did'] == user_input['action'])
                return self.async_show_form(
                    step_id='token',
                    data_schema=vol.Schema({
                        vol.Required('host', default=device['localip']): str,
                        vol.Required('token', default=device['token']): str,
                        vol.Required('ble', default=True): bool,
                        vol.Required('zha', default=False): bool
                    }),
                    description_placeholders={'error_text': ''}
                )

        if DOMAIN in self.hass.data and 'devices' in self.hass.data[DOMAIN]:
            for device in self.hass.data[DOMAIN]['devices']:
                if (device['model'] == 'lumi.gateway.mgl03' and
                        device['did'] not in ACTIONS):
                    name = f"Add {device['name']} ({device['localip']})"
                    ACTIONS[device['did']] = name

        return self.async_show_form(
            step_id='user',
            data_schema=vol.Schema({
                vol.Required('action', default='cloud'): vol.In(ACTIONS)
            })
        )

    async def async_step_token(self, user_input=None, error=None):
        """GUI > Configuration > Integrations > Plus > RS-485 Gateway 1"""
        if user_input is not None:
            error = gateway1.is_gw1(user_input['host'], user_input['token'])
            if error:
                return await self.async_step_token(error=error)

            return self.async_create_entry(title=user_input['host'],
                                           data=user_input)

        return self.async_show_form(
            step_id='token',
            data_schema=vol.Schema({
                vol.Required('host'): str,
                vol.Required('token'): str,
                vol.Required('ble', default=True): bool,
                vol.Required('zha', default=False): bool
            }),
            description_placeholders={
                'error_text': "\nERROR: " + error if error else ''
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler('username' in config_entry.data)


class OptionsFlowHandler(OptionsFlow):
    def __init__(self, cloud: bool):

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            did = user_input['did']
            device = next(d for d in self.hass.data[DOMAIN]['devices']
                          if d['did'] == did)
            device_info = (
                f"Name: {device['name']}\n"
                f"Model: {device['model']}\n"
                f"IP: {device['localip']}\n"
                f"MAC: {device['mac']}\n"
                f"Token: {device['token']}"
            )
        elif not self.hass.data[DOMAIN].get('devices'):
            device_info = "No devices in account"
        else:
            device_info = "Select device from list"

        devices = {
            device['did']: f"{device['name']} ({device['localip']})"
            for device in self.hass.data[DOMAIN].get('devices', [])
            if device['pid'] in ('0', '8')
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required('did'): vol.In(devices)
            }),
            description_placeholders={
                'device_info': device_info
            }
        )
