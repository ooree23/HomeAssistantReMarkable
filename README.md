# reMarkable status integration on Home Assistant

![](logo.png)

Home Assistant integration to track tour reMarkable status.  
Developped by Aurélien Tomassini (ooree23).

It requires :
- your reMarkable to be in the same network as your Home Assistant
- a `device_tracker` entity that has the IP address of your reMarkable as a "ip" attribute.
  It allows to use a dynamic IP address for your reMarkable, usually thanks to your router
  integration.
- activate the SSH over Wifi (disabled by default), in the menu 
  `Settings` > `Help` > `Copyright...` > Conformity section.
  It gives you the SSH login/password, and the command to enable it in Wifi.
  Once allowed, your reMarkable will be accessible by Home Assistant over Wifi,
  every time it is connected to your local network.

Trigger :
- Data is refreshed every time the `device_tracker` changes (state or IP)
- Data is also refreshed every 5 minutes

Sensors :

![](docs/device_sensors.png)

Dashboard example :

![](docs/dashboard.png)