import json
import asyncio_mqtt
import asyncio


class Component:
    def __init__(self, name):
        self.name = name
        self.client = None

    async def start(self):
        async with asyncio_mqtt.Client("recordserver2") as client:
            self.client = client
            self.update_state()
            topic = f"robot/{self.name}/ctrl"
            async with client.filtered_messages(topic) as messages:
                await client.subscribe(topic)
                async for message in messages:
                    self.process_control(json.loads(message.payload.decode()))

    def update_state(self):
        message = json.dumps(self.state)
        asyncio.create_task(self.client.publish(f"robot/{self.name}/state", message))

    def process_control(self, message):
        pass

    @property
    def state(self):
        return {}
