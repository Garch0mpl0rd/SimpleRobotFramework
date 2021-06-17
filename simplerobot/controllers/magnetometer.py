import asyncio
from simplerobot.mqtt import Component

try:
    import board
    from adafruit_lis2mdl import LIS2MDL

    i2c = board.I2C()  # uses board.SCL and board.SDA
except:
    i2c = None

    class LIS2MDL:
        def __init__(self, i2c):
            self.magnetic = (0, 1, 0)


class MagnetometerController(Component):
    def __init__(self, config: dict):
        super().__init__("magnetometers")
        self.magnetometers = {}
        self.state = {}
        for name, details in config['magnetometers'].items():
            if details['type'] == 'lsm303agr':
                sensor = LIS2MDL(i2c)
                self.magnetometers[name] = sensor
                self.state[name] = {axis: value for axis, value in zip('xyz', sensor.magnetic)}

    async def start(self):
        asyncio.create_task(self.measure())
        await super().start()

    async def measure(self):
        while True:
            await asyncio.sleep(0.06)
            update = False
            for name, sensor in self.magnetometers.items():
                new_measurement = {axis: value for axis, value in zip('xyz', sensor.magnetic)}
                if new_measurement != self.state[name]:
                    self.state[name] = new_measurement
                    update = True
            if update:
                self.update_state()
