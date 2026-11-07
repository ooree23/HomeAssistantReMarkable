from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        RemarkableBinarySensor(
          coordinator,
          entry,
          "SSH connexion",
          "ssh_status",
          BinarySensorDeviceClass.CONNECTIVITY,
        ),
        RemarkableBinarySensor(
          coordinator,
          entry,
          "Battery charging",
          "battery_status",
          BinarySensorDeviceClass.BATTERY_CHARGING,
        ),
    ]
    async_add_entities(entities)

class RemarkableBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, entry, name, key, device_class=None):
        super().__init__(coordinator)
        self._attr_name = name
        self._key = key
        self._attr_unique_id = f"remarkable_{entry.entry_id}_{key}"
        self._attr_device_class = device_class
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    @property
    def is_on(self):
        if self._key == "ssh_status":
            val = self.coordinator.ssh_status
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in ("true", "connected", "on", "yes", "1")
            return bool(val)

        elif self._key == "battery_status":
            if self.coordinator.data and self._key in self.coordinator.data and self.coordinator.data.get(self._key) is not None:
                val = str(self.coordinator.data.get(self._key, "")).lower()
                return val in ("charging", "true", "on", "1")

        return None

    @property
    def available(self):
        if self._key == "ssh_status":
            return True
        return super().available