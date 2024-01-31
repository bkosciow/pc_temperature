- What it is

*** WINDOWS ***
Reading PC CPU and GPU temperatures on Windows.
Works as a service.
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


*** LINUX ***
no gpu temperatures

- pip
pip install psutil iot_message pycryptodome

- run
copy config.ini.dist to config.ini
fill data

- service
sudo cp cpu_temperature.service /lib/systemd/system/
sudo systemctl start cpu_temperature
sudo systemctl enable cpu_temperature