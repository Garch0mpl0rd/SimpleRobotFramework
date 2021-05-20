from simplerobot.mqtt import Component

try:
    from rpi_ws281x import PixelStrip, Color
except:
    class PixelStrip:
        def __init__(self, count, pin, frequency, dma, invert, brightness, channel):
            self.count = count
            self.pin = pin
            self.frequency = frequency
            self.dma = dma
            self.invert = invert
            self.brightness = brightness
            self.channel = channel
            self.pixels = [Color(0, 0, 0)] * count

        def getBrightness(self):
            return self.brightness

        def setBrightness(self, brightness):
            self.brightness = brightness

        def setPixelColor(self, index, color):
            self.pixels[index] = color

        def begin(self):
            pass

        def show(self):
            print("Updating pixels")
            for i, color in enumerate(self.pixels):
                print(f"  {i}: {color}")

    class Color:
        def __init__(self, r, g, b):
            self.r = r
            self.g = g
            self.b = b

        def __str__(self):
            return f"red {self.r} green {self.g} blue {self.b}"


class PixelStripLED:
    def __init__(self, parent, index):
        self.parent = parent
        self.index = index
        self.red = 0
        self.green = 0
        self.blue = 0

    def set_color(self, red, green, blue):
        self.red = red
        self.green = green
        self.blue = blue
        self.parent.setPixelColor(self.index, Color(red, green, blue))

    @property
    def state(self):
        return dict(red=self.red, green=self.green, blue=self.blue)


class LEDController(Component):
    def __init__(self, config: dict):
        super().__init__("leds")
        self.controller = None
        self.leds = {}
        led_config = config['leds']
        if led_config['type'] == "pixelstrip":
            self._process_pixelstrip(led_config)

    def _process_pixelstrip(self, config):
        self.controller = PixelStrip(config['count'], config['pin'], config['frequency'], config['dma'],
                                     config['invert'], config['brightness'], config['channel'])
        self.controller.begin()
        for index, name in config['names'].items():
            self.leds[name] = PixelStripLED(self.controller, index)

    def process_control(self, message):
        updated = False
        for name, led in self.leds.items():
            if name in message:
                state = message[name]
                led.set_color(state.get('red', 0), state.get('green', 0), state.get('blue', 0))
                updated = True

        if "brightness" in message:
            self.controller.setBrightness(message["brightness"])
            updated = True

        if updated:
            self.controller.show()
            self.update_state()

    @property
    def state(self):
        return { "brightness": self.controller.getBrightness(),
                 "leds": {name: led.state for name, led in self.leds.items()}}

