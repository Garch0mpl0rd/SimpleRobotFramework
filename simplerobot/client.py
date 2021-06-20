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
        self._observers = []

    def state_updated(self, state: dict):
        self._state = state
        for observer in self._observers:
            observer(self)

    def register(self, observer):
        self._observers.append(observer)

    def unregister(self, observer):
        self._observers.remove(observer)

    @property
    def needs_update(self):
        return bool(self._to_update_state)

    def pop_update_state(self):
        update_state = self._to_update_state
        self._to_update_state = {}
        return update_state

    def __getattr__(self, item):
        if item in self.properties:
            return self._state[item]
        raise AttributeError(f'No attribute {item}')


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
    properties = ('red', 'green', 'blue')

    def set_color(self, red, green, blue):
        self._to_update_state = dict(red=red, green=green, blue=blue)


class Servo(CachedStateObject):
    properties = ('angle', 'target_angle', 'state', 'speed')

    def __init__(self, state: dict):
        super().__init__(state)
        self.event = threading.Event()

    def move_to(self, angle, speed):
        self._to_update_state['angle'] = angle
        self._to_update_state['speed'] = speed

    def state_updated(self, message: dict):
        super().state_updated(message)
        if self.target_angle == self.angle:
            self.event.set()
        else:
            self.event.clear()

    def wait_for_target_reached(self):
        if self.target_angle != self.angle:
            self.event.wait()


class Motor(CachedStateObject):
    properties = ('speed',)

    def set_speed(self, speed):
        self._to_update_state['speed'] = speed


class DistanceSensor(CachedStateObject):
    properties = ('distance', )


class LineSensor(CachedStateObject):
    properties = ('line', )


class Magnetometer(CachedStateObject):
    properties = ('x', 'y', 'z')


class Accelerometer(CachedStateObject):
    properties = ('x', 'y', 'z')


class Robot:
    WAIT_FOR_AREAS = {'servos', 'motors', 'leds', 'distance_sensors', 'line_sensors', 'magnetometers', 'accelerometers'}
    AREA_MAP = {'distancesensors': 'distance_sensors', 'linesensors': 'line_sensors'}

    def __init__(self):
        self.servos = NamedCachedStateObjectCollection(Servo)
        self.motors = NamedCachedStateObjectCollection(Motor)
        self.distance_sensors = NamedCachedStateObjectCollection(DistanceSensor)
        self.line_sensors = NamedCachedStateObjectCollection(LineSensor)
        self.leds = NamedCachedStateObjectCollection(Led)
        self.magnetometers = NamedCachedStateObjectCollection(Magnetometer)
        self.accelerometers = NamedCachedStateObjectCollection(Accelerometer)
        self._led_brightness = None

        client = mqtt.Client()
        self.topic_prefix = 'robot'
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        self._client = client
        self._areas_received = set()
        self.init_event = threading.Event()
        self.servos_updated_event = threading.Event()

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
        if message:
            self._send_message("leds/ctrl", message)

    def update_servos(self):
        message = self._create_message(self.servos)
        if message:
            self.servos_updated_event.clear()
            self._send_message("servos/ctrl", message)
            self.servos_updated_event.wait()

    def wait_for_servos(self):
        for servo in self.servos.values():
            servo.wait_for_target_reached()

    def update_motors(self):
        message = self._create_message(self.motors)
        if message:
            self._send_message("motors/ctrl", message)

    @staticmethod
    def _create_message(named_objects: NamedCachedStateObjectCollection):
        message = {name: item.pop_update_state() for name, item in named_objects.items() if item.needs_update}
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
            if area == 'leds':
                self._led_brightness = message['brightness']
                message = message['leds']

            collection.update_from_message(message)
            self._areas_received.add(area)
            areas_left = Robot.WAIT_FOR_AREAS - self._areas_received
            if not areas_left:
                self.init_event.set()
            if area == 'servos':
                self.servos_updated_event.set()

    def forward(self, speed=100):
        self.motors['left'].set_speed(speed)
        self.motors['right'].set_speed(speed)
        self.update_motors()

    def stop(self):
        self.motors['left'].set_speed(0)
        self.motors['right'].set_speed(0)
        self.update_motors()

    def backward(self, speed=100):
        self.motors['left'].set_speed(speed * -1)
        self.motors['right'].set_speed(speed * -1)
        self.update_motors()

    def rotate_left(self, speed=100):
        self.motors['left'].set_speed(speed * -1)
        self.motors['right'].set_speed(speed)
        self.update_motors()

    def rotate_right(self, speed=100):
        self.motors['left'].set_speed(speed)
        self.motors['right'].set_speed(speed * -1)
        self.update_motors()
