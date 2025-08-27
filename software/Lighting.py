import RPi.GPIO as GPIO

class PWMOutput:
    def __init__(self, gpio_pin, freq, duty):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self.pin = int(gpio_pin)
        self.duty = max(0, min(100, int(duty))) 
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, int(freq))
        self.pwm.start(0) 

    def on(self):
        self.pwm.ChangeDutyCycle(self.duty)

    def off(self):
        self.pwm.ChangeDutyCycle(0)

    def set_duty(self, duty):
        self.duty = max(0, min(100, int(duty)))
        self.on() 

    def stop(self):
        try:
            self.pwm.stop()
        except Exception:
            pass


def init_pwm_outputs(cfg):
    freq = cfg.getint('LightingPWM', 'freq_PWM')

    pins = [
        cfg.getint('LightingPWM', 'port_PWM_0', fallback=0),
        cfg.getint('LightingPWM', 'port_PWM_1', fallback=0),
        cfg.getint('LightingPWM', 'port_PWM_2', fallback=0),
    ]

    duties = [
        cfg.getint('LightingPWM', 'duty_PWM_0', fallback=0),
        cfg.getint('LightingPWM', 'duty_PWM_1', fallback=0),
        cfg.getint('LightingPWM', 'duty_PWM_2', fallback=0),
    ]

    pwm_outputs = []
    for pin, duty in zip(pins, duties):
        if pin != 0:  
            pwm_outputs.append(PWMOutput(pin, freq, duty))

    return pwm_outputs

def lights_on(pwms):
    for p in pwms:
        p.on()

def lights_off(pwms):
    for p in pwms:
        p.off()

def cleanup_pwm(pwms):
    for p in pwms:
        try:
            p.off()
            p.stop()
        except Exception:
            pass
