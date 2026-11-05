from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        RemarkableSensor(coordinator, entry, "Batterie", "battery", "%", SensorDeviceClass.BATTERY),
        RemarkableSensor(coordinator, entry, "Statut Batterie", "battery_status", None, None),
        RemarkableSensor(coordinator, entry, "Stockage Disponible", "storage_free", "%", None, "mdi:harddisk"),
        RemarkableSensor(coordinator, entry, "Stockage Total", "storage_total", None, SensorDeviceClass.DATA_SIZE, "mdi:harddisk"),
        RemarkableSensor(coordinator, entry, "Utilisation RAM", "ram_usage", "%", None, "mdi:memory"),
        RemarkableSensor(coordinator, entry, "Charge CPU", "cpu_load", None, None, "mdi:cpu-64-bit"),
        RemarkableSensor(coordinator, entry, "Linux Version", "linux_version", None, None),
        RemarkableSensor(coordinator, entry, "Version", "version", None, None),
    ]
    async_add_entities(sensors)

class RemarkableSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry, name, key, unit, device_class, icon=None):
        super().__init__(coordinator)
        self._attr_name = f"{entry.title} {name}"
        self._key = key
        # On utilise entry_id pour différencier les entités si vous avez plusieurs tablettes
        self._attr_unique_id = f"remarkable_{entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        if icon:
            self._attr_icon = icon

    @property
    def native_value(self):
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
        # Vérifie si le coordinateur a réussi la dernière maj et si l'IP est valide
        if not super().available:
            return False
        state = self.hass.states.get(self.coordinator.tracker_entity)
        if not state:
            return False
        ip = state.attributes.get("ip")
        return ip not in [None, "None", "unavailable", "unknown", ""]