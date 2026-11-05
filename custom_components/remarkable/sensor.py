from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        RemarkableSensor(coordinator, entry, "Statut SSH", "ssh_status", None, None, "mdi:connection", is_status=True),
        RemarkableSensor(coordinator, entry, "Batterie", "battery", "%", SensorDeviceClass.BATTERY),
        RemarkableSensor(coordinator, entry, "Statut Batterie", "battery_status", None, None, "mdi:power-plug-battery-outline"),
        RemarkableSensor(coordinator, entry, "Stockage Disponible", "storage_free", "%", None, "mdi:harddisk"),
        RemarkableSensor(coordinator, entry, "Stockage Total", "storage_total", "B", SensorDeviceClass.DATA_SIZE, "mdi:harddisk", suggested_unit="GiB"),
        RemarkableSensor(coordinator, entry, "Utilisation RAM", "ram_usage", "%", None, "mdi:memory"),
        RemarkableSensor(coordinator, entry, "Charge CPU", "cpu_load", None, None, "mdi:cpu-64-bit"),
        RemarkableSensor(coordinator, entry, "Linux Version", "linux_version", None, None, "mdi:linux"),
        RemarkableSensor(coordinator, entry, "Firmware Version", "version", None, None, "mdi:cellphone-arrow-down"),
        RemarkableSensor(coordinator, entry, "Model", "device_model", None, None, "mdi:tablet"),
    ]
    async_add_entities(sensors)

class RemarkableSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, name, key, unit, device_class, icon=None, is_status=False, suggested_unit=None):
        super().__init__(coordinator)
        self._attr_name = name
        self._key = key
        self._is_status = is_status
        self._attr_unique_id = f"remarkable_{entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        if suggested_unit:
            self._attr_suggested_unit_of_measurement = suggested_unit
        if icon:
            self._attr_icon = icon

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "reMarkable",
            "model": "Paper Tablet",
        }

    @property
    def device_info(self):
        info = super().device_info
        if self.coordinator.data and "version" in self.coordinator.data:
            info["sw_version"] = self.coordinator.data.get("version")
        model = self.coordinator.data.get("device_model")
        if model:
            info["model"] = f"{model}"
        return info

    @property
    def native_value(self):
        if self._is_status:
            return self.coordinator.ssh_status

        if self.coordinator.data:
            val = self.coordinator.data.get(self._key)
            if self._attr_native_unit_of_measurement == "%" and val:
                try:
                    return float(val)
                except ValueError:
                    return val
            return val
        return None

    @property
    def available(self):
        if self._is_status:
            return True # L'entité de statut reste toujours disponible pour afficher "OK" ou "unavailable"

        if not super().available:
            return False
        state = self.hass.states.get(self.coordinator.tracker_entity)
        if not state:
            return False
        ip = state.attributes.get("ip")
        return ip not in [None, "None", "unavailable", "unknown", ""]