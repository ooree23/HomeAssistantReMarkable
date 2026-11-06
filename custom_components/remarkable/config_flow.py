import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import DOMAIN, DEFAULT_USERNAME, CONF_TRACKER_ENTITY, CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from homeassistant.core import callback

class RemarkableConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title="reMarkable Tablet",
                data=user_input
            )

        schema = vol.Schema({
            vol.Required(CONF_TRACKER_ENTITY, default="device_tracker.remarkable"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="device_tracker")
            ),
            vol.Required(CONF_USERNAME, default=DEFAULT_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=60, mode=selector.NumberSelectorMode.BOX)
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return RemarkableOptionsFlowHandler()

class RemarkableOptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        data = self.config_entry.data

        tracker_default = options.get(CONF_TRACKER_ENTITY, data.get(CONF_TRACKER_ENTITY, "device_tracker.remarkable"))
        username_default = options.get(CONF_USERNAME, data.get(CONF_USERNAME, DEFAULT_USERNAME))
        password_default = options.get(CONF_PASSWORD, data.get(CONF_PASSWORD, ""))
        scan_interval_default = options.get(CONF_SCAN_INTERVAL, data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))

        schema = vol.Schema({
            vol.Required(CONF_TRACKER_ENTITY, default=tracker_default): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="device_tracker")
            ),
            vol.Required(CONF_USERNAME, default=username_default): str,
            vol.Required(CONF_PASSWORD, default=password_default): str,
            vol.Required(CONF_SCAN_INTERVAL, default=scan_interval_default): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=60, mode=selector.NumberSelectorMode.BOX)
            ),
        })

        return self.async_show_form(step_id="init", data_schema=schema)