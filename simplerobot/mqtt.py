import json
import asyncio_mqtt
import asyncio
import os
from urllib.parse import urlparse


class Component:
    def __init__(self, name):
        self.name = name
        self.client = None
        url = os.environ.get('SIMPLEROBOT_MQTT_HOST', "mqtt://localhost")
        self.url_details = urlparse(url)
        self.loop = None
        if self.url_details.scheme not in ('mqtt', 'mqtts'):
            raise RuntimeError('Unsupported URL for MQTT "%s"' % url)

    def _get_connection_details(self):
        kwargs = {}
        host = self.url_details.hostname
        if self.url_details.scheme == 'mqtts':
            kwargs['ssl'] = True
        if self.url_details.port is not None:
            kwargs['port'] = self.url_details.port
        if self.url_details.username is not None:
            kwargs['username'] = self.url_details.username
        if self.url_details.password is not None:
            kwargs['password'] = self.url_details.password
        return host, kwargs

    async def start(self):
        self.loop = asyncio.get_event_loop()
        host, kwargs = self._get_connection_details()
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
        future = self.client.publish(f"robot/{self.name}/state", message)
        if thread_safe:
            asyncio.run_coroutine_threadsafe(future, self.loop)
        else:
            asyncio.create_task(future)

    def process_control(self, message):
        pass

    @property
    def state(self):
        return {}
