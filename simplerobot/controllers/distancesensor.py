from simplerobot.mqtt import Component
import asyncio

try:
    from gpiozero.pins.pigpio import PiGPIOFactory
    from gpiozero import DistanceSensor

except:
    class DistanceSensor:
        def __init__(self, echo, trigger, max_distance=1, pin_factory=None):
            self.distance = 0

    class PiGPIOFactory:
        pass


class DistanceSensorController(Component):
    def __init__(self, config: dict):
        super().__init__("distancesensors")
        self.sensors = {}
        self._state = {}
        for name, sensor in config['distancesensors'].items():
            self.sensors[name] = DistanceSensor(sensor['echo'], sensor['trigger'], max_distance=sensor['max_distance'],
                                                pin_factory=PiGPIOFactory())
            self._state[name] = {"distance": -1}

    async def start(self):
        asyncio.create_task(self.measure())
        await super().start()

    async def measure(self):
        while True:
            await asyncio.sleep(0.06)
            update = False
            for name, sensor in self.sensors.items():
                new_measurement = sensor.distance
                if new_measurement != self._state[name]['distance']:
                    self._state[name]['distance'] = new_measurement
                    update = True
            if update:
                self.update_state()

    @property
    def state(self):
        return self._state
