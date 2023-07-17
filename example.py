from simplerobot.client import Robot
import time

if __name__ == '__main__':
    # Connect to the robot
    robot = Robot()
    print("Connecting to the robot ...")
    robot.connect()
    print("Connected!")

    # Do something
    print("Forward ⬆")
    robot.forward()

    time.sleep(1)

    print("Stop 🛑")
    robot.stop()

    # Make sure the command is sent.
    time.sleep(1)
    print("Bye 👋")
