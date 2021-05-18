import utils
from mqtt import Component
import asyncio

try:
    from gpiozero import DistanceSensor
except:
    class DistanceSensor:
        def __init__(self, echo, trigger, max_distance=1):
            self.distance = 0


class DistanceSensorController(Component):
    def __init__(self):
        super().__init__("distancesensors")
        self.sensors = {}
        for name, sensor in utils.load("distancesensors.yaml", "sensors").items():
            self.sensors[name] = DistanceSensor(sensor['echo'], sensor['trigger'], max_distance=sensor['max_distance'])

    async def start(self):
        asyncio.create_task(self.measure())
        await super().start()

    async def measure(self):
        while True:
            await asyncio.sleep(1)
            self.update_state()


    @property
    def state(self):
        return {name: {"distance": sensor.distance} for name, sensor in self.sensors.items()}


if __name__ == "__main__":
    controller = DistanceSensorController()
    asyncio.run(controller.start())
