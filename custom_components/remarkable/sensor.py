from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from .const import DOMAIN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        RemarkableSensor(coordinator, entry, "SSH connexion", "ssh_status", None, None, "mdi:connection", is_status=True),
        RemarkableSensor(coordinator, entry, "Battery", "battery", "%", SensorDeviceClass.BATTERY),
        RemarkableSensor(coordinator, entry, "Battery status", "battery_status", None, None, "mdi:power-plug-battery-outline"),
        RemarkableSensor(coordinator, entry, "Storage available", "storage_free", "%", None, "mdi:harddisk"),
        RemarkableSensor(coordinator, entry, "Total storage", "storage_total", "GiB", SensorDeviceClass.DATA_SIZE, "mdi:harddisk", entity_category=EntityCategory.DIAGNOSTIC),
        RemarkableSensor(coordinator, entry, "RAM usage", "ram_usage", "%", None, "mdi:memory"),
        RemarkableSensor(coordinator, entry, "CPU usage", "cpu_load", None, None, "mdi:cpu-64-bit", state_class=SensorStateClass.MEASUREMENT),
        RemarkableSensor(coordinator, entry, "Linux Version", "linux_version", None, None, "mdi:linux", entity_category=EntityCategory.DIAGNOSTIC),
        RemarkableSensor(coordinator, entry, "Firmware Version", "version", None, None, "mdi:cellphone-arrow-down", entity_category=EntityCategory.DIAGNOSTIC),
        RemarkableSensor(coordinator, entry, "Model", "device_model", None, None, "mdi:tablet", entity_category=EntityCategory.DIAGNOSTIC),
        RemarkableScanIntervalSensor(coordinator, entry),
    ]
    async_add_entities(sensors)

class RemarkableSensor(CoordinatorEntity, SensorEntity, RestoreEntity):
    def __init__(self, coordinator, entry, name, key, unit, device_class, icon=None, is_status=False, entity_category=None, state_class=None):
        super().__init__(coordinator)
        self._attr_name = name
        self._key = key
        self._is_status = is_status
        self._attr_unique_id = f"remarkable_{entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        if state_class:
            self._attr_state_class = state_class
        if entity_category:
            self._attr_entity_category = entity_category
        if icon:
            self._attr_icon = icon

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "reMarkable",
            "model": "Paper Tablet",
        }
        self._restored_value = None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in ["unavailable", "unknown"]:
            self._restored_value = last_state.state
        if self._key in ("device_model", "version"):
            await self.coordinator.async_update_device_registry()

    @property
    def device_info(self):
        return self._attr_device_info

    @property
    def native_value(self):
        if self._is_status:
            return self.coordinator.ssh_status

        val = None
        if self.coordinator.data and self._key in self.coordinator.data:
            val = self.coordinator.data.get(self._key)
        elif self._restored_value is not None:
            val = self._restored_value

        if val is not None:
            try:
                if (self._attr_native_unit_of_measurement == "%"
                    or self._attr_device_class == SensorDeviceClass.DATA_SIZE
                    or self._key == "cpu_load"
                ):
                    return float(val)
                return val
            except (ValueError, TypeError):
                return val
        return None

    @property
    def available(self):
        if self._is_status:
            return True

        if (self.coordinator.data and self._key in self.coordinator.data) or self._restored_value is not None:
            return True

        return super().available




class RemarkableScanIntervalSensor(SensorEntity):
    _attr_icon = "mdi:update"
    _attr_has_entity_name = True
    _attr_translation_key = "scan_interval"  # Optionnel pour l'internationalisation

    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"remarkable_{entry.entry_id}_scan_interval"
        self._attr_name = "Refresh Interval"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        # Optionnel : rattacher au même appareil que les autres sensors
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    @property
    def native_value(self):
        # Récupère la valeur depuis les options ou les données (en minutes)
        return self._entry.options.get(
            CONF_SCAN_INTERVAL,
            self._entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )

    @property
    def native_unit_of_measurement(self):
        return "min"