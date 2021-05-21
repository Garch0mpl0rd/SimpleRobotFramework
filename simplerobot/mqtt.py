import json
import asyncio_mqtt
import asyncio
import os
from urllib.parse import urlparse
from .utils import get_mqtt_connection_details


class Component:
    def __init__(self, name):
        self.name = name
        self.client = None
        self.loop = None

    async def start(self):
        self.loop = asyncio.get_event_loop()
        url = os.environ.get('SIMPLEROBOT_MQTT_HOST', "mqtt://localhost")
        host, kwargs = get_mqtt_connection_details(url)
        async with asyncio_mqtt.Client(host, **kwargs) as client:
            self.client = client
            self.update_state()
            topic = f"robot/{self.name}/ctrl"
            async with client.filtered_messages(topic) as messages:
                await client.subscribe(topic)
                async for message in messages:
                    self.process_control(json.loads(message.payload.decode()))

    def update_state(self, thread_safe=False):
        message = json.dumps(self.state)
        future = self.client.publish(f"robot/{self.name}/state", message, retain=True)
        if thread_safe:
            asyncio.run_coroutine_threadsafe(future, self.loop)
        else:
            asyncio.create_task(future)

    def process_control(self, message):
        pass

    @property
    def state(self):
        return {}
