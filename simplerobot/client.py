import json
import os
import threading
from typing import Dict, Iterator
from collections.abc import Mapping
from .utils import get_mqtt_connection_details
import paho.mqtt.client as mqtt


class CachedStateObject:
    def __init__(self, state: dict):
        self._state = state
        self._to_update_state = {}

    def state_updated(self, state: dict):
        self._state = state

    @property
    def needs_update(self):
        return bool(self._to_update_state)

    def pop_update_state(self):
        update_state = self._to_update_state
        self._to_update_state = {}
        return update_state


class NamedCachedStateObjectCollection(Mapping):
    def __init__(self, state_class):
        self.names_to_obj: Dict[str:CachedStateObject] = {}
        self.state_class = state_class

    def __getitem__(self, key: str) -> CachedStateObject:
        return self.names_to_obj[key]

    def __len__(self) -> int:
        return len(self.names_to_obj)

    def __iter__(self) -> Iterator[str]:
        return iter(self.names_to_obj)

    def update_from_message(self, message: dict):
        for name, state in message.items():
            obj = self.names_to_obj.get(name)
            if obj is None:
                self.names_to_obj[name] = self.state_class(state)
            else:
                obj.state_updated(state)


class Led(CachedStateObject):
    def set_color(self, red, green, blue):
        self._to_update_state = dict(red=red, green=green, blue=blue)

    @property
    def red(self):
        return self._state.get('red', 0)

    @property
    def green(self):
        return self._state.get('green', 0)

    @property
    def blue(self):
        return self._state.get('blue', 0)


class Servo(CachedStateObject):
    def move_to(self, angle, speed):
        self._to_update_state['angle'] = angle
        self._to_update_state['speed'] = speed

    @property
    def angle(self):
        return self._state['angle']

    @property
    def target_angle(self):
        return self._state['target_angle']

    @property
    def state(self):
        return self._state['state']

    @property
    def speed(self):
        return self._state['speed']


class Motor(CachedStateObject):
    def set_speed(self, speed):
        self._to_update_state['speed'] = speed

    @property
    def speed(self):
        return self._state['speed']


class DistanceSensor(CachedStateObject):
    @property
    def distance(self):
        return self._state['distance']


class LineSensor(CachedStateObject):
    @property
    def line_detected(self):
        return self._state['line']


class Robot:
    WAIT_FOR_AREAS = {'servos', 'motors', 'leds', 'distance_sensors', 'line_sensors'}
    AREA_MAP = {'distancesensors':'distance_sensors', 'linesensors': 'line_sensors'}

    def __init__(self):
        self.servos = NamedCachedStateObjectCollection(Servo)
        self.motors = NamedCachedStateObjectCollection(Motor)
        self.distance_sensors = NamedCachedStateObjectCollection(DistanceSensor)
        self.line_sensors = NamedCachedStateObjectCollection(LineSensor)
        self.leds = NamedCachedStateObjectCollection(Led)
        self._led_brightness = None

        client = mqtt.Client()
        self.topic_prefix = 'robot'
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        self._client = client
        self._areas_received = set()
        self.init_event = threading.Event()

    def connect(self, url=None):
        if url is None:
            url = os.environ.get('SIMPLEROBOT_MQTT_HOST', "mqtt://localhost")
        host, kwargs = get_mqtt_connection_details(url)
        self._client.connect(host, **kwargs)
        self._client.loop_start()
        self.init_event.wait()

    @property
    def led_brightness(self):
        return self._led_brightness

    def update_leds(self, brightness=None):
        message = self._create_message(self.leds)
        if brightness is not None:
            message['brightness'] = brightness
        for name, led in self.leds.items():
            if led.needs_update:
                message[name] = led.pop_update_state()
        if message:
            self._send_message("leds/ctrl", message)

    def update_servos(self):
        message = self._create_message(self.servos)
        if message:
            self._send_message("servos/ctrl", message)

    def update_motors(self):
        message = self._create_message(self.motors)
        if message:
            self._send_message("motors/ctrl", message)

    @staticmethod
    def _create_message(named_objects: NamedCachedStateObjectCollection):
        message = {name: item.pop_update_state() for name, item in named_objects if item.needs_update}
        return message

    def _send_message(self, topic: str, message: dict):
        data = json.dumps(message)
        self._client.publish(f'{self.topic_prefix}/{topic}', data)

    def _on_connect(self, client, *args):
        client.subscribe(f'{self.topic_prefix}/+/state')

    def _on_message(self, client, userdata, msg):
        message = json.loads(msg.payload.decode())
        area = msg.topic.split('/')[-2]
        area = Robot.AREA_MAP.get(area, area)
        collection = getattr(self, area, None)
        if isinstance(collection, NamedCachedStateObjectCollection):
            collection.update_from_message(message)
            self._areas_received.add(area)
            areas_left = Robot.WAIT_FOR_AREAS - self._areas_received
            if not areas_left:
                self.init_event.set()

    def forward(self, speed=1):
        self.motors['left'].set_speed(speed)
        self.motors['right'].set_speed(speed)
        self.update_motors()

    def stop(self):
        self.motors['left'].set_speed(0)
        self.motors['right'].set_speed(0)
        self.update_motors()

    def backward(self, speed=1):
        self.motors['left'].set_speed(speed * -1)
        self.motors['right'].set_speed(speed * -1)
        self.update_motors()


