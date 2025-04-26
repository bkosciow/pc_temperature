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
import pprint
import subprocess
import logging

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
        self.fast_loop = int(config.get("global.fast_loop"))
        self.slow_loop = int(config.get("global.slow_loop"))
        self.running = True
        self.slow_tick = self.slow_loop + 1
        socket.setdefaulttimeout(60)
        self.dev_dir = "/dev/"

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

    def get_hdd_temp(self, hdd):
        for line in subprocess.Popen(
                ['smartctl', '-a', str(self.dev_dir + hdd)],
                stdout=subprocess.PIPE
        ).stdout.read().decode('utf8').split('\n'):
            if ('Temperature_Celsius' in line.split()) or ('Temperature_Internal' in line.split()):
                return line.split()[9]
            if 'Temperature:' in line.split():
                return line.split()[1]

        return None

    def get_readings(self):
        return psutil.sensors_temperatures()

    def build_message(self):
        temp = self.get_readings()
        data = {
            "cpu_load": psutil.cpu_percent(),
        }

        for item in self.mapping:
            if len(item['type']) == 3 and item['type'].startswith("sd"):
                if self.slow_tick > self.slow_loop:
                    data[item['key']] = self.get_hdd_temp(item['type'])
            elif item['type'].startswith("nvme"):
                if self.slow_tick > self.slow_loop:
                    data[item['key']] = self.get_hdd_temp(item['type'])
            else:
                v = temp[item['type']][0]
                data[item['key']] = v.current

        if self.slow_tick > self.slow_loop:
            self.slow_tick = 0
        self.slow_tick += 1

        return data

    def main(self):
        while self.running:
            self.send(self.build_message())
            time.sleep(self.fast_loop)


if __name__ == '__main__':
    path = "./"
    debug = False
    dev = "/dev/"
    opts, args = getopt.getopt(sys.argv[1:], "hc:d", ["config=", "debug"])
    for opt, arg in opts:
        if opt == '-d' or opt == '--debug':
            debug = True
        if opt == '-c' or opt == "--config":
            path = arg
        if opt == '-h':
            drv = "/dev_host/"

    p = PythonService(path)
    p.dev_dir = dev
    if debug:
        pprint.pprint(p.get_readings())
        pprint.pprint(p.build_message())
    else:
        p.main()
