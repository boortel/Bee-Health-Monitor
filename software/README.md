# BeeLogger software

## Setup
Download and install Raspberry OS Buster for rPI4 (grove.py is not compatible with the Bullseye!)

Install the latest grove.py:

```
curl -sL https://github.com/Seeed-Studio/grove.py/raw/master/install.sh | sudo bash -s -
```

Install dependencies for OpenCV and PyAudio:

```
sudo apt-get install -y libatlas-base-dev libhdf5-dev libhdf5-serial-dev libatlas-base-dev libjasper-dev  libqtgui4  libqt4-test
sudo apt-get install portaudio19-dev
```

Clone this repo and install the requirements:

```
git clone https://github.com/boortel/Bee-Health-Monitor.git
pip install -r requirements.txt
```

Set the usb drive name, illumination times, logging termination time (optional) and the sensor logging period in the file BeeLogger.ini

```
# USB drive name
driveName = BEELOGGER
# Illumination turn on and off times
lightOn_hour = 6
lightOn_minute = 30
lightOff_hour = 18
lightOff_minute = 30
# Logging stop time
logOff_year = 2022
logOff_month = 4
logOff_day = 1
logOff_hour = 12
logOff_minute = 10
# Flag to set timed logging
logStop = True
# Thread call period [s]
period_threadSensors = 30
```

Run the main.py

```
python3 main.py
```

To start the program automatically on boot transfer bee-monitor.service file to systemd files:

```
sudo cp -p -r -f  "/home/pi/Bee-Health-Monitor/software/bee-monitor.service" "/usr/lib/systemd/system/bee-monitor.service"
```

Update the systemd files and enable bee-monitor.service bee:

```
sudo systemctl daemon-reload
sudo systemctl enable bee-monitor.service
```

Finally the program can be started:

```
sudo systemctl start bee-monitor.service
```

## Block diagram

A schematic block diagram of the proposed program (without the remote logging and Raspberry Pico update) is shown in figure bellow:

![BeeLogger](https://github.com/boortel/Bee-Health-Monitor/assets/33236294/30634ed4-a469-448c-90a5-f2c87a7281da)

