import gatt
import logging

class CowDevice(gatt.Device):
    SERVICE_UUID = "0000cd00-caa9-44b2-8b43-96ae3072fd3"
    CHARACTERISTIC_TO_UUID = {
        "led": r"0000cd01-caa9-44b2-8b43-96ae3072fd36",
        "time": r"0000cd02-caa9-44b2-8b43-96ae3072fd36",
        "date": r"0000cd03-caa9-44b2-8b43-96ae3072fd36",
        "tx_power": r"0000cd04-caa9-44b2-8b43-96ae3072fd36",
        "adv_interval": r"0000cd05-caa9-44b2-8b43-96ae3072fd36",
        "switch": r"0000cd06-caa9-44b2-8b43-96ae3072fd36",
        "error": r"0000cd07-caa9-44b2-8b43-96ae3072fd36",
        "password": r"0000cd08-caa9-44b2-8b43-96ae3072fd36",
    }
    UUID_TO_CHARACTERISTIC = {
        r"0000cd01-caa9-44b2-8b43-96ae3072fd36": "led" ,
        r"0000cd02-caa9-44b2-8b43-96ae3072fd36": "time",
        r"0000cd03-caa9-44b2-8b43-96ae3072fd36": "date",
        r"0000cd04-caa9-44b2-8b43-96ae3072fd36": "tx_power",
        r"0000cd05-caa9-44b2-8b43-96ae3072fd36": "adv_interval",
        r"0000cd06-caa9-44b2-8b43-96ae3072fd36": "switch",
        r"0000cd07-caa9-44b2-8b43-96ae3072fd36": "error",
       r"0000cd08-caa9-44b2-8b43-96ae3072fd36": "password",
    }

    def __init__(self, mac_address, manager, managed=True):
        gatt.Device.__init__(self,mac_address, manager, managed)

        self.logger = logging.getLogger('cowdevice')
        self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        self.characteristics = {}

    def connect_succeeded(self):
        super().connect_succeeded()
        self.logger.error("[%s] Connected" % (self.mac_address))

    def connect_failed(self, error):
        super().connect_failed(error)
        self.logger.error("[%s] Connection failed: %s" % (self.mac_address, str(error)))

    def disconnect_succeeded(sself):
        super().disconnect_succeeded()
        self.logger.info("[%s] Disconnected" % (self.mac_address))

    def services_resolved(self):
        super().services_resolved()
        self.parse_servieces()

        self.read_all()
        self.set_led(False)
        self.set_time(4, 23, 1)
        self.set_date(12, 4, 4)

    def parse_servieces(self):
        self.logger.debug("[%s] Resolved services" % (self.mac_address))
        for service in self.services:
            self.logger.debug("[%s]  Service [%s]" % (self.mac_address, service.uuid))
            for characteristic in service.characteristics:
                self.logger.debug("[%s]    Characteristic [%s]" % (self.mac_address, characteristic.uuid))
                name = self.UUID_TO_CHARACTERISTIC[characteristic.uuid]
                self.characteristics[name] = characteristic

    def characteristic_value_updated(self, characteristic, value):
        name = self.UUID_TO_CHARACTERISTIC[characteristic.uuid]
        method_name = ("on_%s_update" % name)
        if method_name in dir(self):
             getattr(self, method_name)(characteristic, value)

    def on_led_update(self, characteristic, value):
        self.logger.info("Led state: %s", "ON" if value == 1 else "OFF")

    def on_time_update(self, characteristic, value):
        self.logger.info("Time: %s", value.decode('ascii'))

    def on_date_update(self, characteristic, value):
        self.logger.info("Date: %s", value.decode('ascii'))

    def on_tx_power_update(self, characteristic, value):
        power = "%+d" % int.from_bytes(value,  byteorder='little', signed=True)
        self.logger.info("Tx power: %sdBm", power)

    def on_adv_interval_update(self, characteristic, value):
        interval = int.from_bytes(value, byteorder='little', signed=False)
        self.logger.info("Advertise interval: %sms", interval)
    
    def on_error_update(self, characteristic, value):
        self.logger.info("Error: 0x%s", value.hex())

    def on_password_update(self, characteristic, value):
        self.logger.info("Password: 0x%s", value.hex())

    def read_time(self):
        self.characteristics['time'].read_value()

    def read_all(self):
        for name, characteristic in self.characteristics.items():
            characteristic.read_value()

    def set_led(self, state=True):
        if state:
            self.characteristics['led'].write_value(b"\x01")
        else:
            self.characteristics['led'].write_value(b"\x00")

    def set_adv_interval(self, interval=250):
        value = interval.to_bytes(2, byteorder='little')
        self.characteristics['adv_interval'].write_value(value)

    def set_switch(self, state):
        value = state.to_bytes(1, byteorder='little')
        self.characteristics['switch'].write_value(value)
        
    def set_time(self, hour, minute, second):
        if hour > 23 or hour < 0:
            raise ValueError("Hour out of range <0, 23>")
        if minute > 59 or minute < 0:
            raise ValueError("Minute out of range <0, 59>")
        if second > 59 or second < 0:
            raise ValueError("Second out of range <0, 59>")

        value = '{:02}:{:02}:{:02}'.format(hour, minute, second)
        self.characteristics['time'].write_value(value.encode('ascii'))

    def set_date(self, day, month, year):
        if day > 31 or day < 0:
            raise ValueError("Day out of range <0, 31>")
        if month > 12 or month < 0:
            raise ValueError("Month out of range <0, 12>")
        if year > 99 or year < 0:
            raise ValueError("Year out of range <0, 99>")

        value = '{:02}/{:02}/{:02}'.format(day, month, year)
        self.characteristics['date'].write_value(value.encode('ascii'))

    def characteristic_write_value_succeeded(self, characteristic):
        name = self.UUID_TO_CHARACTERISTIC[characteristic.uuid]
        self.logger.debug("Write for %s succeded", name)

    def characteristic_write_value_failed(self, characteristic, error):
        name = self.UUID_TO_CHARACTERISTIC[characteristic.uuid]
        self.logger.error("Write for %s failed: %s", name, error)

