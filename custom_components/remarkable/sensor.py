from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.restore_state import RestoreEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        RemarkableSensor(coordinator, entry, "SSH connexion", "ssh_status", None, None, "mdi:connection", is_status=True),
        RemarkableSensor(coordinator, entry, "Battery", "battery", "%", SensorDeviceClass.BATTERY),
        RemarkableSensor(coordinator, entry, "Battery status", "battery_status", None, None, "mdi:power-plug-battery-outline"),
        RemarkableSensor(coordinator, entry, "Storage available", "storage_free", "%", None, "mdi:harddisk"),
        RemarkableSensor(coordinator, entry, "Total storage", "storage_total", "B", SensorDeviceClass.DATA_SIZE, "mdi:harddisk", suggested_unit="GiB", entity_category=EntityCategory.DIAGNOSTIC),
        RemarkableSensor(coordinator, entry, "RAM usage", "ram_usage", "%", None, "mdi:memory"),
        RemarkableSensor(coordinator, entry, "CPU usage", "cpu_load", None, None, "mdi:cpu-64-bit"),
        RemarkableSensor(coordinator, entry, "Linux Version", "linux_version", None, None, "mdi:linux", entity_category=EntityCategory.DIAGNOSTIC),
        RemarkableSensor(coordinator, entry, "Firmware Version", "version", None, None, "mdi:cellphone-arrow-down", entity_category=EntityCategory.DIAGNOSTIC),
        RemarkableSensor(coordinator, entry, "Model", "device_model", None, None, "mdi:tablet", entity_category=EntityCategory.DIAGNOSTIC),
    ]
    async_add_entities(sensors)

class RemarkableSensor(CoordinatorEntity, SensorEntity, RestoreEntity):
    def __init__(self, coordinator, entry, name, key, unit, device_class, icon=None, is_status=False, suggested_unit=None, entity_category=None):
        super().__init__(coordinator)
        self._attr_name = name
        self._key = key
        self._is_status = is_status
        self._attr_unique_id = f"remarkable_{entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        if suggested_unit:
            self._attr_suggested_unit_of_measurement = suggested_unit
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

    @property
    def device_info(self):
        return self._attr_device_info

    @property
    def native_value(self):
        if self._is_status:
            return self.coordinator.ssh_status

        val = None
        if self.coordinator.data:
            val = self.coordinator.data.get(self._key)

        if val is None:
            val = self._restored_value

        if val is not None:
            if self._attr_native_unit_of_measurement == "%" or self._attr_device_class == SensorDeviceClass.DATA_SIZE:
                try:
                    return float(val)
                except ValueError:
                    return val
            return val
        return None

    @property
    def available(self):
        if self._is_status:
            return True

        if (self.coordinator.data and self._key in self.coordinator.data) or self._restored_value is not None:
            return True

        return super().available