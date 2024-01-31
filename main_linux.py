import time
from configparser import ConfigParser
from importlib import import_module
import json
from iot_message.message import Message
import socket
import os


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
    def __init__(self):
        self.running = True
        config = Config("./config.ini")
        self.address = (config.get("message.ip"), int(config.get("message.port")))
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
            with open(r"/sys/class/thermal/thermal_zone0/temp") as File:
                temp = File.readline()
                data = {
                    "cpu_temperature": float(temp)/1000
                }
            self.send(data)
            time.sleep(3)


if __name__ == '__main__':
    p = PythonService()
    p.main()

