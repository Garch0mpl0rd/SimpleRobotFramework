from yaml import safe_load
from urllib.parse import urlparse
import numpy


def load(filename):
    with open(filename) as f:
        result = safe_load(f)
    return result


class ConnectionDetailsError(Exception):
    pass


def get_mqtt_connection_details(url):
    url_details = urlparse(url)
    kwargs = {}
    host = url_details.hostname

    if url_details.scheme not in ('mqtt', 'mqtts'):
        raise ConnectionDetailsError('Unsupported URL for MQTT "%s"' % url)
    if url_details.scheme == 'mqtts':
        kwargs['ssl'] = True
    if url_details.port is not None:
        kwargs['port'] = url_details.port
    if url_details.username is not None:
        kwargs['username'] = url_details.username
    if url_details.password is not None:
        kwargs['password'] = url_details.password
    return host, kwargs


class MovingAverage:
    def __init__(self, window_size):
        self._count = 0
        self._offset = 0
        self.window_size = window_size
        self._array = numpy.array([0.0] * window_size)

    def add(self, value):
        self._array[self._offset] = value
        if self._count < self.window_size:
            self._count += 1
        self._offset = (self._offset + 1) % self.window_size

    @property
    def is_valid(self):
        return self._count > self.window_size

    @property
    def average(self):
        return numpy.mean(self._array)
