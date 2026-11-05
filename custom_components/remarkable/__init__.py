import logging
import asyncio
import paramiko
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN, CONF_TRACKER_ENTITY, CONF_USERNAME, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    tracker_entity = entry.data[CONF_TRACKER_ENTITY]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    coordinator = RemarkableDataUpdateCoordinator(hass, entry, tracker_entity, username, password)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Écoute les changements d'état du device_tracker pour déclencher un refresh immédiat si l'IP change
    @callback
    async def async_tracker_changed(event):
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state and old_state:
            new_ip = new_state.attributes.get("ip")
            old_ip = old_state.attributes.get("ip")
            if new_ip != old_ip:
                _LOGGER.info("IP de la reMarkable modifiée (%s -> %s), rafraîchissement...", old_ip, new_ip)
                await coordinator.async_request_refresh()

    entry.async_on_unload(
        async_track_state_change_event(hass, [tracker_entity], async_tracker_changed)
    )

    return True

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
            update_interval=timedelta(minutes=5), # Intervalle global (ou ajustable)
        )
        self.tracker_entity = tracker_entity
        self.username = username
        self.password = password

    async def _async_update_data(self):
        state = self.hass.states.get(self.tracker_entity)
        if not state:
            raise UpdateFailed(f"Entité tracker {self.tracker_entity} introuvable")

        ip = state.attributes.get("ip")
        if not ip or ip in ["None", "unavailable", "unknown", ""]:
            raise UpdateFailed("Adresse IP de la reMarkable non disponible")

        # Exécution groupée des commandes via une seule connexion SSH
        def fetch_ssh():
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                ssh.connect(ip, username=self.username, password=self.password, timeout=10)

                commands = {
                    "battery": "cat /sys/class/power_supply/*/capacity",
                    "battery_status": "cat /sys/class/power_supply/*/status",
                    "storage_free": "df /home | awk 'NR==2 {printf \"%.1f\", ($4/$2)*100}'",
                    "storage_total": "df -h /home | awk 'NR==2 {print $2}'",
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
                raise UpdateFailed(f"Erreur de connexion SSH : {err}")

        return await self.hass.async_add_executor_job(fetch_ssh)