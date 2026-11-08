[![rm1](https://img.shields.io/badge/rM1-supported-green)](https://remarkable.com/products/remarkable-1)
[![rm2](https://img.shields.io/badge/rM2-supported_not_tested-green)](https://remarkable.com/products/remarkable-2)
[![rmpp](https://img.shields.io/badge/rMPP-supported_not_tested-green)](https://remarkable.com/products/remarkable-paper/pro)
[![rmppm](https://img.shields.io/badge/rMPPM-supported_not_tested-green)](https://remarkable.com/products/remarkable-paper/pro-move)
[![rmppure](https://img.shields.io/badge/rMPPure-supported_not_tested-green)](https://remarkable.com/products/remarkable-paper/pure)
[![Discord](https://img.shields.io/discord/385916768696139794.svg?label=reMarkable&logo=discord&logoColor=ffffff&color=7389D8&labelColor=6A7EC2)](https://discord.gg/ATqQGfu)
&nbsp;  
![ha_badge](https://img.shields.io/badge/reMarkable_Firmware-v3.30.0+_Compatible-orange)  
![ha_badge](https://img.shields.io/badge/Home_Assistant-2026.11.0_Compatible-blue)  


# reMarkable status, Home Assistant unofficial integration

![](logo.png)

Home Assistant integration to track your reMarkable tablet status.  
Developped by Aurélien Tomassini (ooree23).  
**This is a custom integration, not official, nor related to reMarkable team.  
Please ensure to read the Caution section !**


Tested with reMarkable 1, on Home Assistant 2026.11.0.

<!-- toc -->

- [Features](#features)
- [Caution](#caution)
- [Installation](#installation)
  * [Requirements](#requirements)
  * [Adding your reMarkable(s)](#adding-your-remarkables)
- [Trigger](#trigger)
- [Sensors](#sensors)
  * [Device example](#device-example)
  * [Dashboard example](#dashboard-example)

<!-- tocstop -->

## Features

Track your reMarkable info :
- **Battery** sensor :  
  you can then see its evolution over the week,  
  create notification when battery is low,  
  notify when the battery fully charged...  
  ![](docs/battery_hist.png)
- **Storage** usage sensor :  
  see the storage evolution over time,  
  notify when storage remaining is low, etc  
  ![](docs/storage_hist.png)
- **CPU** usage sensor
- **RAM** usage sensor
- **Firmware** version
- **Linux** version
- **Model**
- Connexion history


## Caution

<div style="background-color:rgba(200,80,0,0.5); padding: 16px; margin-bottom: 6px; border-radius: 12px">
<b>CAUTION</b>
<hr style="height: 1px; margin: 6px 0;"/>
This integration connects to your reMarkable using SSH connexion.<br/>
All the SSH commands used are in the file <a href="./ssh_commands.py">ssh_commands.py</a>.<br/>
When using a fork (or even my version), please ensure to be aware of which command is used,
to ensure that the integration doesn't modify any data on your reMarkable.
<b>Use it at your own risk.</b>
</div>

<div style="background-color:rgba(70,120,0,0.5); padding: 16px; border-radius: 12px">
Every single command in this integration is read-only :
<ul>
<li>reading file "/sys/class/power_supply/" for battery information</li>
<li>using read command "df" for storage information</li>
<li>using read command "free" for RAM information</li>
<li>reading file "/proc/loadavg" for CPU information</li>
<li>reading file "/etc/os-release" for OS and firmware information</li>
<li>reading file "/sys/devices/soc0/machine" for device information</li>
</ul>
</div>

## Installation

[![Open your Home Assistant instance and open a repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=ooree23&repository=HomeAssistantReMarkable&category=integration)

### Requirements

- Your reMarkable **must be** in the same network as your Home Assistant
- A `device_tracker` entity that has the IP address of your reMarkable as **a "ip" attribute**.  
  It allows to use a dynamic IP address for your reMarkable, usually thanks to your router
  integration.  
  > If you have no device_tracker to find the IP from, you can force static IP for your reMarkable on your routeur.  
  > In this case, you can create a virtual `device_tracker` in your `configuration.yaml`, containing this static IP address.
  > ```yaml
  > template:
  >   - device_tracker:
  >       - name: "My rM tracker with static IP"
  >         unique_id: my_remarkable_virtual_tracker
  >         in_zones: "{{ ['zone.home'] }}" 
  >         attributes:
  >           ip: "192.168.1.50"
  >           mac: "AA:BB:CC:DD:EE:FF"
  > ```
- The **SSH over Wifi must be enabled** (disabled by default).   
  If not enabled yet, go to `Settings` > `Help` > `Copyright...` > Conformity section.  
  It gives you the SSH login/password, and the command to enable it in Wifi.  
  Once allowed, your reMarkable will be accessible by Home Assistant over Wifi,
  every time it is connected to your local network.

### Adding your reMarkable(s)

> You can add as many reMarkable tablets as you want.  
> Each of them must have its own `device_tracker`.

- Add new integration, and search for reMarkable
- Fill the form :
  - select the `device_tracker` targeting this new reMarkable (cf above explanation)
  - fill username and password  
  ![](docs/add_device.png)

## Trigger
- Data is refreshed every time the `device_tracker` changes (state or IP)
- Data is also refreshed every 5 minutes by default (interval customizable)

## Sensors

### Device example

![](docs/device_sensors.png)

### Dashboard example

![](docs/dashboard.png)