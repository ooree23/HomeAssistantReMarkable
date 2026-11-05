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
    tracker_entity = entry.options.get(CONF_TRACKER_ENTITY, entry.data.get(CONF_TRACKER_ENTITY))
    username = entry.options.get(CONF_USERNAME, entry.data.get(CONF_USERNAME))
    password = entry.options.get(CONF_PASSWORD, entry.data.get(CONF_PASSWORD))

    coordinator = RemarkableDataUpdateCoordinator(hass, entry, tracker_entity, username, password)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

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

    async def _async_update_data(self):
        # Récupération dynamique si les options ont changé
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
            return data
        except Exception as err:
            _LOGGER.warning("Erreur de connexion SSH : %s", err)
            self.ssh_status = "unavailable"
            # Si on a déjà des données précédentes, on les retourne pour éviter les "trous" dans les graphiques
            if self.data:
                return self.data
            raise UpdateFailed(f"Erreur de connexion SSH : {err}")