- What it is
Reading PC CPU and GPU temperatures on Windows.
Work as a service.
Require OpenHardwareMonitorLib.dll (https://openhardwaremonitor.org/downloads/)

- pip
require
pip install iot_message pycryptodome

iot_message is required only for broadcasting data to local network. you remove and do what u want instead

- run
copy config.ini.dist to config.ini
fill data

open terminal as an admin,
go to project dir, type:
python .\main.py install
python .\main.py start
