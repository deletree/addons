# RS-485 Gateway 1.0 integration for Home Assistant

Control RS-485 devices from Home Assistant.

# How it works

The component starts the **MQTT Server** on the public port of the Gateway. All the logic in the Gateway runs on top of the built-in MQTT Server. By default, access to it is closed from the outside.

**ATTENTION:** MQTT work without a password! Do not use this method on public networks.

After rebooting the device, all changes will be reset. The component will launch MQTT every time it detects that it is disabled.

# Debug mode

Component support debug mode. Shows only component logs. The link to the logs is always random.

With `debug: rs-485` or debug `debug: mqtt` option you will get advanced log for raw 485 and MQTT data.

With `debug: true` option you will get usual component logs.

```yaml
rs485-gateway 1.0:
  debug: true  # you will get HA notification with a link to the logs page
```

You can filter data in the logs, enable auto refresh (in seconds) and tail last lines.
