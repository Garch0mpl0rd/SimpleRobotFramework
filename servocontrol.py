import utils
from mqtt import Component
import asyncio

try:
    import Adafruit_PCA9685

    pwm = Adafruit_PCA9685.PCA9685()
    pwm.set_pwm_freq(50)
except:
    class PWMEmulator:
        def set_pwm(self, servo, start, stop):
            print(f"Servo {servo} Start {start} Stop {stop}")

    pwm = PWMEmulator()


class Servo:
    def __init__(self, index, pwm_min, pwm_max, angle_range, angle_min, angle_max):
        self.index = index
        self.pwm_min = pwm_min
        self.angle_range = angle_range
        self.pwm_multiplier = (pwm_max - pwm_min) / angle_range
        self.angle_min = angle_min
        self.angle_max = angle_max
        self.state = 'idle'
        self.angle = 0
        self.target_angle = 0
        self.speed = 0
        self.tick_count = 0
        self.tick_count_divider = 0
        self.init_position()

    def init_position(self):
        self.angle = 0
        self.target_angle = 0
        self.state = 'idle'
        self.set_pwm(0)

    def set_angle(self, angle, speed):
        angle = max(min(angle, self.angle_max), self.angle_min)
        self.target_angle = angle
        self.speed = speed
        self.tick_count_divider = 1.0 / speed
        self.state = 'move' if angle != self.angle else 'idle'

    def update_angle(self):
        if self.state == 'idle':
            return False
        self.tick_count += 1
        if self.tick_count >= self.tick_count_divider:
            angle_change = int(self.tick_count / self.tick_count_divider)
            self.tick_count = 0
            if self.angle > self.target_angle:
                self.angle -= angle_change
                if self.angle < self.target_angle:
                    self.angle = self.target_angle
            elif self.angle < self.target_angle:
                self.angle += angle_change
                if self.angle > self.target_angle:
                    self.angle = self.target_angle

            self.set_pwm(self.angle)

            if self.target_angle == self.angle:
                self.state = 'idle'
        return True

    def set_pwm(self, angle):
        pwm.set_pwm(self.index, 0, self.pwm_min + int(self.pwm_multiplier * (angle + self.angle_range / 2)))

    @property
    def state_dict(self):
        return dict(state=self.state, angle=self.angle, target_angle=self.target_angle, speed=self.speed,
                    angle_min=self.angle_min, angle_max=self.angle_max)


class ServoController(Component):
    def __init__(self):
        super().__init__("servos")
        self.servos = {}
        for index, servo in utils.load("servos.yaml", "servos").items():
            pwm_details = servo['pwm']
            angle_details = servo['angle']
            self.servos[servo['name']] = Servo(index, pwm_details['min'], pwm_details['max'],
                                               angle_details['range'], angle_details['min'], angle_details['max'])

    async def start(self):
        asyncio.create_task(self.update_servos())
        await super().start()

    def process_control(self, message):
        update = False
        for name, servo in self.servos.items():
            if name in message:
                angle = message[name]['angle']
                speed = message[name]['speed']
                servo.set_angle(angle, speed)
                update = True
        if update:
            self.update_state()

    async def update_servos(self):
        while True:
            need_state_update = False
            for servo in self.servos.values():
                if servo.update_angle():
                    need_state_update = True
            if need_state_update:
                self.update_state()
            await asyncio.sleep(0.037)

    @property
    def state(self):
        return {name: servo.state_dict for name, servo in self.servos.items()}


if __name__ == "__main__":
    controller = ServoController()
    asyncio.run(controller.start())
