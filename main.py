import clr
import time
from configparser import ConfigParser
from importlib import import_module
import json
from iot_message.message import Message
import socket
import win32serviceutil
import win32service
import win32event
import servicemanager
import os

# usage:
# python .\main.py install
# python .\main.py start

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


class PythonService(win32serviceutil.ServiceFramework):
    _svc_name_ = "PCMONITOR"
    _svc_display_name_ = "PC Monitoring"

    @classmethod
    def parse_command_line(cls):
        win32serviceutil.HandleCommandLine(cls)

    def __init__(self, args):
        self.running = True
        config = Config(os.path.dirname(__file__) + "/config.ini")
        self.mapping = config.get_dict("global.windows_mappings")
        self.address = (config.get("message.ip"), int(config.get("message.port")))
        self.running = True
        dll = config.get("global.dll")
        if not dll:
            dll = os.path.dirname(__file__) + "/OpenHardwareMonitorLib.dll"
        self.handle = self.initialize_openhardwaremonitor(dll)
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.running = False
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
        )
        self.main()

    def initialize_openhardwaremonitor(self, file):
        clr.AddReference(file)
        from OpenHardwareMonitor import Hardware
        handle = Hardware.Computer()
        handle.MainboardEnabled = True
        handle.CPUEnabled = True
        handle.RAMEnabled = True
        handle.GPUEnabled = True
        handle.HDDEnabled = True
        handle.Open()
        return handle

    def get_readings(self):
        data = {}

        for i in self.handle.Hardware:
            i.Update()
            for sensor in i.Sensors:
                if sensor.Value is not None:
                    for item in self.mapping:
                        if item["type"] == str(sensor.SensorType) and item["name"] == str(sensor.Name):
                            data[item["key"]] = sensor.Value

            for j in i.SubHardware:
                j.Update()
                for subsensor in j.Sensors:
                    for item in self.mapping:
                        if item["type"] == str(subsensor.SensorType) and item["name"] == str(subsensor.Name):
                            data[item["key"]] = subsensor.Value

        return data

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
            data = self.get_readings()
            self.send(data)
            time.sleep(3)


if __name__ == '__main__':
    PythonService.parse_command_line()
