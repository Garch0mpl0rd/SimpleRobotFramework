import time
from simplerobot.client import Robot
from simplerobot.compass import Compass


class Explorer:
    def __init__(self, robot):
        self.robot = robot
        self.compass = Compass(robot.magnetometers['body'])
        self.state = 'init'

    def run(self):
        while True:
            func = getattr(self, f'state_{self.state}')
            func()

    def state_init(self):
        robot = self.robot
        robot.stop()
        for led in robot.leds.values():
            led.set_color(0, 0, 0)
        for servo in robot.servos.values():
            servo.move_to(0, 90)
        robot.update_leds()
        robot.update_servos()
        robot.wait_for_servos()
        self.state = 'calibrate'

    def state_calibrate(self):
        robot = self.robot
        compass = self.compass
        compass.calibration_start()
        robot.rotate_right(50)
        for second in range(12):
            level = ('bottom', 'top')[(second // 3) % 2]
            position = ('back', 'middle', 'front')[second % 3]
            color = ((255, 0, 0), (0, 255, 0))[second // 6]
            for side in ('left', 'right'):
                robot.leds[f'{side}_{level}_{position}'].set_color(*color)
            robot.update_leds()
            time.sleep(1)
        compass.calibration_finish()
        robot.stop()
        self.state = 'forward'
        print(f'Current bearing: {self.compass.bearing}')

    def state_forward(self):
        self.state = None
        while True:
            print(f'Current bearing: {self.compass.bearing}')
            time.sleep(0.5)


if __name__ == '__main__':
    robot = Robot()
    robot.connect()
    explorer = Explorer(robot)
    explorer.run()
