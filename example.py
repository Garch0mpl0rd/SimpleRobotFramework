from simplerobot.client import Robot
import time

if __name__ == '__main__':
    # Connect to the robot
    robot = Robot()
    print("Connecting to the robot ...")
    robot.connect()
    print("Connected!")

    print("Turning LEDs on 🔴 🟢 🔵")
    robot.leds['left_bottom_back'].set_color(255, 0, 0)
    robot.leds['left_top_middle'].set_color(0, 255, 0)
    robot.leds['left_bottom_front'].set_color(0, 0, 255)

    robot.leds['right_top_back'].set_color(255, 0, 0)
    robot.leds['right_bottom_middle'].set_color(0, 255, 0)
    robot.leds['right_top_front'].set_color(0, 0, 255)
    robot.update_leds()

    # Do something
    print("Forward ⬆")
    robot.forward()

    time.sleep(1)

    print("Stop 🛑")
    robot.stop()

    # Turn off leds
    robot.leds['left_bottom_back'].set_color(0, 0, 0)
    robot.leds['left_top_middle'].set_color(0, 0, 0)
    robot.leds['left_bottom_front'].set_color(0, 0, 0)
    robot.leds['right_top_back'].set_color(0, 0, 0)
    robot.leds['right_bottom_middle'].set_color(0, 0, 0)
    robot.leds['right_top_front'].set_color(0, 0, 0)
    robot.update_leds()

    # Make sure the command is sent.
    time.sleep(1)
    print("Bye 👋")
