import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from . import DOMAIN
#from .core import gateway1

_LOGGER = logging.getLogger(__name__)

PORTS = {
    'port1': "Add Port1 device type.",
    'port2': "Add Port2 device type."
}


class RS485Gateway1FlowHandler(ConfigFlow, domain=DOMAIN):
 
    async def async_step_port1(self, user_input=None):
        if user_input is not None:
           return self.async_show_form(
                    step_id='port2',
                    data_schema=vol.Schema({
                        vol.Required('port2', default='tty/01': vol.In(ACTIONS)
                    }),
                    description_placeholders={'error_text': ''}
                )

        return self.async_show_form(
            step_id='port1',
            data_schema=vol.Schema({
                vol.Required('port1', default='tty/usb'): vol.In(ACTIONS)
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler('username' in config_entry.data)


class OptionsFlowHandler(OptionsFlow):
    #to do
