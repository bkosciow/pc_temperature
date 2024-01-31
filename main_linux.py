import time
from configparser import ConfigParser
from importlib import import_module
import json
from iot_message.message import Message
import socket
import os
import psutil
import getopt
import sys

# sudo cp cpu_temperature.service /lib/systemd/system/
# sudo systemctl start cpu_temperature
# sudo systemctl enable cpu_temperature


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)


class Config(object):
    """Class Config"""
    def __init__(self, file="config.ini"):
        self.file = file
        self.config = ConfigParser()
        self.config.read(file)
        self.init_message()

    def get(self, name):
        if "." in name:
            section, name = name.split(".")
        else:
            section = "global"

        val = self.config.get(section, name)
        return val if val != "" else None

    def __getitem__(self, item):
        return self.config[item]

    def get_section(self, section):
        """return section"""
        return dict(self.config.items(section))

    def get_dict(self, name):
        value = self.get(name)
        return json.loads(value)

    def init_message(self):
        Message.node_name = self.get("message.node_name")
        if self.get("message.encoder"):
            encClass = getattr(import_module(self.get("message.encoder")), "Cryptor")
            params = self.get("message.encoder_params")
            if params is None:
                encInstance = encClass()
            else:
                params = params.split(",")
                encInstance = encClass(*params)

            Message.add_encoder(encInstance)


class PythonService:
    def __init__(self, cfg_path="./"):
        self.running = True
        config = Config(cfg_path+"config.ini")
        self.address = (config.get("message.ip"), int(config.get("message.port")))
        self.mapping = config.get_dict("global.linux_mappings")
        self.running = True
        socket.setdefaulttimeout(60)

    def send(self, data):
        msg = {
            'event': 'pc.monitoring',
            'parameters': data,
        }
        message = Message()
        message.set(msg)
        try:
            s.sendto(bytes(message), self.address)
        except Exception:
            pass

    def main(self):
        while self.running:
            temp = psutil.sensors_temperatures()
            data = {
                "cpu_load": psutil.cpu_percent(),
            }

            for item in temp[self.mapping["cpu_temperature"]["type"]]:
                if item.label == self.mapping["cpu_temperature"]["label"]:
                    data["cpu_temperature"] = item.current

            self.send(data)
            time.sleep(3)


if __name__ == '__main__':
    path = "./"
    opts, args = getopt.getopt(sys.argv[1:], "c:", ["config="])
    for opt, arg in opts:
        if opt == '-c' or opt == "--config":
            path = arg

    p = PythonService(path)
    p.main()

