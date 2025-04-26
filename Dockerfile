FROM python:3.10
RUN apt update && apt install -y smartmontools
RUN mkdir /app
RUN pip install psutil iot_message pycryptodome
WORKDIR /app
COPY config.ini .
COPY main_linux.py /app/main.py

CMD ["python", "./main.py", "-h"]
