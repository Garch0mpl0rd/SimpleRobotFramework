import asyncio
from simplerobot import utils
from simplerobot.controllers import *


async def main():
    config = utils.load("config/robot.yaml")
    controllers = [ctrl(config) for ctrl in (MotorController, ServoController, DistanceSensorController,
                   LEDController, LineSensorController, MagnetometerController, AccelerometerController)]
    for controller in controllers:
        asyncio.create_task(controller.start())

    while True:
        await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
