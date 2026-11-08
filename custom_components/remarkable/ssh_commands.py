SSH_COMMANDS = {
    "battery": "cat /sys/class/power_supply/*/capacity",
    "battery_status": "cat /sys/class/power_supply/*/status",
    "storage_free": "df /home | awk 'NR==2 {printf \"%.1f\", ($4/$2)*100}'",
    "storage_total": "df /home | awk 'NR==2 {print $2 / (1024 * 1024)}'",
    "ram_usage": "free | awk '/Mem:/ {printf \"%.1f\", ($3/$2)*100}'",
    "cpu_load": "awk '{print $1}' /proc/loadavg",
    "linux_version": "sed -n 's/^VERSION=\"\(.*\)\"/\\1/p' /etc/os-release",
    "version": "sed -n 's/^IMG_VERSION=\"\(.*\)\"/\\1/p' /etc/os-release",
    "device_model": "cat /sys/devices/soc0/machine 2>/dev/null || echo 'reMarkable'",
}