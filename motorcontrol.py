import utils
from mqtt import Component
import asyncio

try:
    from gpiozero import Motor
except:
    class Motor:
        def __init__(self, a, b, enable, _):
            self.a = a
            self.b = b
            self.enable = enable
            self.value = 0


class MotorController(Component):
    def __init__(self):
        super().__init__("motors")
        self.motors = {}
        for motor in utils.load("motors.yaml", "motors"):
            self.motors[motor['name']] = Motor(motor['pin1'], motor['pin2'], motor['enable'], True)

    def process_control(self, message):
        updated = False
        for name in self.motors.keys():
            if name in message:
                speed = message[name]
                if isinstance(speed, dict):
                    speed = speed.get("speed")

                if isinstance(speed, (int, float)):
                    updated = True
                    self.motors[name].value = speed / 100
        if updated:
            self.update_state()

    @property
    def state(self):
        return {name: {"speed": motor.value * 100} for name, motor in self.motors.items()}


if __name__ == "__main__":
    controller = MotorController()
    asyncio.run(controller.start())
