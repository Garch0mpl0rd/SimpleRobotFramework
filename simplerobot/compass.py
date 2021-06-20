from .utils import MovingAverage
import math
# inspiration and code taken from https://github.com/adafruit/Adafruit_CircuitPython_LIS2MDL/blob/main/examples/


class MinMax:
    def __init__(self):
        self.min = 1000
        self.max = -1000

    def update(self, value):
        self.min = min(self.min, value)
        self.max = max(self.max, value)

    def normalise(self, value):
        axis = min(max(value, self.min), self.max)
        return (axis - self.min) * 200 / (self.max - self.min) + -100

    def __str__(self):
        return f'{self.min} - {self.max}'


class Compass:
    def __init__(self, magnetometer):
        self.calibrating = False
        self.calibration = None
        self.magnetometer = magnetometer
        self.magnetometer.register(self._sensor_updated)
        self.average = {axis: MovingAverage(10) for axis in 'xyz'}

    def calibration_start(self):
        self.calibration = {'x': MinMax(), 'y': MinMax(), 'z': MinMax()}
        self.calibrating = True

    def calibration_finish(self):
        self.calibrating = False
        for axis in 'xyz':
            print(f'{axis} : {self.calibration[axis]}')

    def _sensor_updated(self, sensor):
        if self.calibrating:
            for axis in 'xyz':
                self.calibration[axis].update(getattr(sensor, axis))

        for axis in 'xyz':
            self.average[axis].add(getattr(sensor, axis))

    @property
    def bearing(self):
        # we will only use X and Y for the compass calculations, so hold it level!
        bearing = int(math.atan2(self.calibration['x'].normalise(self.average['x'].average),
                                 self.calibration['y'].normalise(self.average['y'].average)) * 180.0 / math.pi)
        # compass_heading is between -180 and +180 since atan2 returns -pi to +pi
        # this translates it to be between 0 and 360
        bearing += 180
        return bearing
