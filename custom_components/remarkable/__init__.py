import logging
import asyncio
import paramiko
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, CONF_TRACKER_ENTITY, CONF_USERNAME, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    tracker_entity = entry.options.get(CONF_TRACKER_ENTITY, entry.data.get(CONF_TRACKER_ENTITY))
    username = entry.options.get(CONF_USERNAME, entry.data.get(CONF_USERNAME))
    password = entry.options.get(CONF_PASSWORD, entry.data.get(CONF_PASSWORD))

    # Attente de la création de l'entité tracker (timeout de 30 secondes)
    elapsed = 0
    while elapsed < 30:
        if hass.states.get(tracker_entity) is not None:
            break
        await asyncio.sleep(1)
        elapsed += 1
    else:
        _LOGGER.warning("Le tracker %s n'est pas apparu après 30 secondes, continuation...", tracker_entity)

    coordinator = RemarkableDataUpdateCoordinator(hass, entry, tracker_entity, username, password)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.warning("Impossible de joindre la reMarkable au démarrage, les entités utiliseront les états restaurés : %s", err)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Mise à jour initiale du registre (via les données du coordinateur ou les états restaurés)
    await coordinator.async_update_device_registry()

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    @callback
    async def async_tracker_changed(event):
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state and old_state:
            _LOGGER.info("Changement détecté sur le tracker %s, rafraîchissement...", tracker_entity)
            await coordinator.async_request_refresh()

    entry.async_on_unload(
        async_track_state_change_event(hass, [tracker_entity], async_tracker_changed)
    )

    return True

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

class RemarkableDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, tracker_entity: str, username: str, password: str):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )
        self.entry = entry
        self.tracker_entity = tracker_entity
        self.username = username
        self.password = password
        self.ssh_status = "unavailable"

    async def async_update_device_registry(self):
        """Met à jour le registre des appareils avec les données disponibles ou restaurées."""
        model = None
        version = None

        if self.data:
            model = self.data.get("device_model")
            version = self.data.get("version")
        else:
            # Fallback sur les états restaurés des entités si le coordinateur n'a pas de données
            model_state = self.hass.states.get(f"sensor.remarkable_{self.entry.entry_id}_device_model")
            version_state = self.hass.states.get(f"sensor.remarkable_{self.entry.entry_id}_version")
            if model_state and model_state.state not in ["unavailable", "unknown"]:
                model = model_state.state
            if version_state and version_state.state not in ["unavailable", "unknown"]:
                version = version_state.state

        device_registry = dr.async_get(self.hass)
        device_registry.async_get_or_create(
            config_entry_id=self.entry.entry_id,
            identifiers={(DOMAIN, self.entry.entry_id)},
            manufacturer="reMarkable",
            model=model if model else "Paper Tablet",
            sw_version=version,
            name=self.entry.title,
        )

    async def _async_update_data(self):
        self.tracker_entity = self.entry.options.get(CONF_TRACKER_ENTITY, self.entry.data.get(CONF_TRACKER_ENTITY))
        self.username = self.entry.options.get(CONF_USERNAME, self.entry.data.get(CONF_USERNAME))
        self.password = self.entry.options.get(CONF_PASSWORD, self.entry.data.get(CONF_PASSWORD))

        state = self.hass.states.get(self.tracker_entity)
        if not state:
            self.ssh_status = "unavailable"
            if self.data:
                return self.data
            raise UpdateFailed(f"Entité tracker {self.tracker_entity} introuvable")

        ip = state.attributes.get("ip")
        if not ip or ip in ["None", "unavailable", "unknown", ""]:
            self.ssh_status = "unavailable"
            if self.data:
                return self.data
            raise UpdateFailed("Adresse IP de la reMarkable non disponible")

        def fetch_ssh():
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(ip, username=self.username, password=self.password, timeout=10)

                commands = {
                    "battery": "cat /sys/class/power_supply/*/capacity",
                    "battery_status": "cat /sys/class/power_supply/*/status",
                    "storage_free": "df /home | awk 'NR==2 {printf \"%.1f\", ($4/$2)*100}'",
                    "storage_total": "df /home | awk 'NR==2 {print $2 * 1024}'",
                    "ram_usage": "free | awk '/Mem:/ {printf \"%.1f\", ($3/$2)*100}'",
                    "cpu_load": "awk '{print $1}' /proc/loadavg",
                    "linux_version": "sed -n 's/^VERSION=\"\(.*\)\"/\\1/p' /etc/os-release",
                    "version": "sed -n 's/^IMG_VERSION=\"\(.*\)\"/\\1/p' /etc/os-release",
                    "device_model": "cat /sys/devices/soc0/machine 2>/dev/null || echo 'reMarkable'"
                }

                results = {}
                for key, cmd in commands.items():
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    results[key] = stdout.read().decode('utf-8').strip()

                ssh.close()
                return results
            except Exception as err:
                raise err

        try:
            data = await self.hass.async_add_executor_job(fetch_ssh)
            self.ssh_status = "Connected"
            self.data = data
            await self.async_update_device_registry()
            return data
        except Exception as err:
            _LOGGER.warning("Erreur de connexion SSH : %s", err)
            self.ssh_status = "unavailable"
            if self.data:
                return self.data
            raise UpdateFailed(f"Erreur de connexion SSH : {err}")