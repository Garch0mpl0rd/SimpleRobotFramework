import asyncio
from simplerobot.mqtt import Component

try:
    import board
    from adafruit_lsm303_accel import LSM303_Accel

    i2c = board.I2C()  # uses board.SCL and board.SDA
except:
    i2c = None

    class LSM303_Accel:
        def __init__(self, i2c):
            self.acceleration = (0, 0, 9.8)


class AccelerometerController(Component):
    def __init__(self, config: dict):
        super().__init__("accelerometers")
        self.accelerometers = {}
        self.state = {}
        for name, details in config['accelerometers'].items():
            if details['type'] == 'lsm303':
                sensor = LSM303_Accel(i2c)
                self.accelerometers[name] = sensor
                self.state[name] = {axis: value for axis, value in zip('xyz', sensor.acceleration)}

    async def start(self):
        asyncio.create_task(self.measure())
        await super().start()

    async def measure(self):
        while True:
            await asyncio.sleep(0.06)
            update = False
            for name, sensor in self.accelerometers.items():
                new_measurement = {axis: value for axis, value in zip('xyz', sensor.acceleration)}
                if new_measurement != self.state[name]:
                    self.state[name] = new_measurement
                    update = True
            if update:
                self.update_state()
