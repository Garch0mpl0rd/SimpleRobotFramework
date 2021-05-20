from simplerobot.mqtt import Component
import asyncio

try:
    from gpiozero.pins.pigpio import PiGPIOFactory
    from gpiozero import LineSensor

except:
    class LineSensor:
        def __init__(self, pin):
            self.value = 0


class LineSensorController(Component):
    def __init__(self, config: dict):
        super().__init__("linesensors")
        self.sensors = {}
        for name, sensor_config in config['linesensors'].items():
            sensor = LineSensor(sensor_config['pin'])
            sensor.when_line = sensor.when_no_line = self._when_line_changed
            self.sensors[name] = sensor

    def _when_line_changed(self):
        self.update_state(True)

    @property
    def state(self):
        return {name: {"line": sensor.value} for name, sensor in self.sensors.items()}
