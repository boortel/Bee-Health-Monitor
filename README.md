# BeeLogger

### Setup
Download and install Raspberry OS Buster for rPI4 (grove.py is not compatible with the Bullseye!)

Install the latest grove.py:

```
curl -sL https://github.com/Seeed-Studio/grove.py/raw/master/install.sh | sudo bash -s -
```

Clone this repo and install the requirements:

```
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
