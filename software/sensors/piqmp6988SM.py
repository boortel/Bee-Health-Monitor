# -*- coding: utf-8 -*-

import time
from enum import Enum
from smbus2 import SMBus, i2c_msg, I2cFunc

SMBUS = True
DEBUG = False

# QMP6988
ADDRESS_0            = 0x70
ADDRESS_1            = 0x56

TEMP_TXD0            = 0xFC
TEMP_TXD1            = 0xFB
TEMP_TXD2            = 0xFA
PRESS_TXD0           = 0xF9
PRESS_TXD1           = 0xF8
PRESS_TXD2           = 0xF7
IO_SETUP             = 0xF5
CTRL_MEAS            = 0xF4
DEVICE_STAT          = 0xF3
I2C_SET              = 0xF2
IIR_CNT              = 0xF1
RESET                = 0xE0
CHIP_ID              = 0xD1
COE_b00_a0_ex        = 0xB8
COE_a2_0             = 0xB7
COE_a2_1             = 0xB6
COE_a1_0             = 0xB5
COE_a1_1             = 0xB4
COE_a0_0             = 0xB3
COE_a0_1             = 0xB2
COE_bp3_0            = 0xB1
COE_bp3_1            = 0xB0
COE_b21_0            = 0xAF
COE_b21_1            = 0xAE
COE_b12_0            = 0xAD
COE_b12_1            = 0xAC
COE_bp2_0            = 0xAB
COE_bp2_1            = 0xAA
COE_b11_0            = 0xA9
COE_b11_1            = 0xA8
COE_bp1_0            = 0xA7
COE_bp1_1            = 0xA6
COE_bt2_0            = 0xA5
COE_bt2_1            = 0xA4
COE_bt1_0            = 0xA3
COE_bt1_1            = 0xA2
COE_b00_0            = 0xA1
COE_b00_1            = 0xA0

SUBTRACTOR           = 8388608 # (2 ** 23)

REG_COE              = COE_b00_1
COE_LENGTH           = 25

REG_CHIP_ID          = CHIP_ID
CHIP_ID_LENGTH       = 1

REG_RESET            = RESET
RESET_VALUE          = 0xE6

REG_CTRL_MEAS        = CTRL_MEAS
CTRL_MEAS_LENGTH     = 1

REG_IIR_CNT          = IIR_CNT
IIR_CNT_LENGTH       = 1

REG_DATA             = PRESS_TXD2
DATA_LENGTH          = 6

class Coe(Enum):
    b00_1            = 0
    b00_0            = 1
    bt1_1            = 2
    bt1_0            = 3
    bt2_1            = 4
    bt2_0            = 5
    bp1_1            = 6
    bp1_0            = 7
    b11_1            = 8
    b11_0            = 9
    bp2_1            = 10
    bp2_0            = 11
    b12_1            = 12
    b12_0            = 13
    b21_1            = 14
    b21_0            = 15
    bp3_1            = 16
    bp3_0            = 17
    a0_1             = 18
    a0_0             = 19
    a1_1             = 20
    a1_0             = 21
    a2_1             = 22
    a2_0             = 23
    b00_a0_ex        = 24

class Address(Enum):
    LOW              = ADDRESS_0    
    HIGH             = ADDRESS_1    

class Powermode(Enum):
    SLEEP            = 0
    FORCE            = 1
    NORMAL           = 3

class Filter(Enum):
    COEFFECT_OFF     = 0
    COEFFECT_2       = 1
    COEFFECT_4       = 2
    COEFFECT_8       = 3
    COEFFECT_16      = 4
    COEFFECT_32      = 5

class Oversampling(Enum):
    SKIP             = 0
    X1               = 1
    X2               = 2
    X4               = 3
    X8               = 4
    X16              = 5
    X32              = 6
    X64              = 7

class Data(Enum):
    PRESS_TXD2       = 0
    PRESS_TXD1       = 1
    PRESS_TXD0       = 2
    TEMP_TXD2        = 3
    TEMP_TXD1        = 4
    TEMP_TXD0        = 5

K_PARAM = {
    'a0'  : { 'A' :  0.0     , 'S' : 1.0     , 'D' :    16.0 },    
    'a1'  : { 'A' : -6.30E-03, 'S' : 4.30E-04, 'D' : 32767.0 },    
    'a2'  : { 'A' : -1.90E-11, 'S' : 1.20E-10, 'D' : 32767.0 },    
    'b00' : { 'A' :  0.0     , 'S' : 1.0     , 'D' :    16.0 },    
    'bt1' : { 'A' :  1.00E-01, 'S' : 9.10E-02, 'D' : 32767.0 },    
    'bt2' : { 'A' :  1.20E-08, 'S' : 1.20E-06, 'D' : 32767.0 },    
    'bp1' : { 'A' :  3.30E-02, 'S' : 1.90E-02, 'D' : 32767.0 },    
    'b11' : { 'A' :  2.10E-07, 'S' : 1.40E-07, 'D' : 32767.0 },    
    'bp2' : { 'A' : -6.30E-10, 'S' : 3.50E-10, 'D' : 32767.0 },    
    'b12' : { 'A' :  2.90E-13, 'S' : 7.60E-13, 'D' : 32767.0 },    
    'b21' : { 'A' :  2.10E-15, 'S' : 1.20E-14, 'D' : 32767.0 },    
    'bp3' : { 'A' :  1.30E-16, 'S' : 7.90E-17, 'D' : 32767.0 }    
}

class PiQmp6988(object):
    def __init__(self, bus, config={}):
        self.k  = {}
        self.config = {}
        self.bus = SMBus(bus)
        time.sleep(0.02)
        config_i = {
            'address' : Address.LOW.value,
            'filter' : Filter.COEFFECT_OFF.value,
            'mode': Powermode.SLEEP.value,
            'pressure' : Oversampling.SKIP.value,
            'temperature' : Oversampling.SKIP.value
        }
        self.__modify_config(config_i)
        self.__modify_config(config)
        #self.__pre_process()

      
        # QMP6988
        if SMBUS:
            if DEBUG:
                print('Attempt to read ID')
            data = self.bus.read_i2c_block_data(self.config['address'], REG_CHIP_ID, CHIP_ID_LENGTH)
            if DEBUG:
                print('Read ID')
                print(data)
        else:
            len, data = self.pi.i2c_read_i2c_block_data(self.qmp6988, REG_CHIP_ID, CHIP_ID_LENGTH)

        if SMBUS:
            if DEBUG:
                print('Attempt to read coefs')
            data = self.bus.read_i2c_block_data(self.config['address'], REG_COE, COE_LENGTH)
            if DEBUG:
                print('Read coefs')
                for d in data:
                   print(d)
        else:
            len, data = self.pi.i2c_read_i2c_block_data(self.qmp6988, REG_COE, COE_LENGTH)
        
        self.__initialize_k(data)
        self.__apply_config()
        #self.__post_process()

    def __pre_process(self):
        """
        pigpio
        """

        if SMBUS:
            #self.bus.instance.open(1)
            time.sleep(0.02)
        else:
            self.pi = pigpio.pi()
            # I2C bus
            self.qmp6988 = self.pi.i2c_open(1, self.config['address'])


    def __post_process(self):
        """
        pigpio
        """
        if SMBUS:
            #self.bus.instance.close()
            temptemp=1
        else:
            self.pi.i2c_close(self.qmp6988)
            self.pi.stop()

    def __modify_config(self, config={}):
        for key in config.keys():
            if config[key] is not None:
                self.config[key] = config[key]

    def __apply_config(self):
        self.__set_powermode(self.config['mode'])
        self.__set_filter(self.config['filter'])
        self.__set_oversampling('temperature', self.config['temperature'])
        self.__set_oversampling('pressure', self.config['pressure'])

    def __calc_k(self, index, otp):
        return K_PARAM[index]['A'] + (K_PARAM[index]['S'] * otp) / K_PARAM[index]['D'] 

    def __initialize_k(self, data):
        otp = (data[Coe.a0_1.value] << 12) | (data[Coe.a0_0.value]) << 4 | (data[Coe.b00_a0_ex.value] & 0x0F)
        otp = self.__convert_signed(otp, 19)
        self.k['a0'] = self.__calc_k('a0', otp)
        K_PARAM['a0']['OTP'] = otp
        
        otp = (data[Coe.a1_1.value] << 8) | (data[Coe.a1_0.value])
        otp = self.__convert_signed(otp, 15)
        self.k['a1'] = self.__calc_k('a1', otp)
        K_PARAM['a1']['OTP'] = otp
        
        otp = (data[Coe.a2_1.value] << 8) | (data[Coe.a2_0.value])
        otp = self.__convert_signed(otp, 15)
        self.k['a2'] = self.__calc_k('a2', otp)
        K_PARAM['a2']['OTP'] = otp
        
        otp = (data[Coe.b00_1.value] << 12) | (data[Coe.b00_0.value]) << 4 | ((data[Coe.b00_a0_ex.value] & 0xF0) >> 4)
        otp = self.__convert_signed(otp, 19)
        self.k['b00'] = self.__calc_k('b00', otp)
        
        otp = (data[Coe.bt1_1.value] << 8) | (data[Coe.bt1_0.value])
        otp = self.__convert_signed(otp, 15)
        self.k['bt1'] = self.__calc_k('bt1', otp)
        
        otp = (data[Coe.bt2_1.value] << 8) | (data[Coe.bt2_0.value])
        otp = self.__convert_signed(otp, 15)
        self.k['bt2'] = self.__calc_k('bt2', otp)
        
        otp = (data[Coe.bp1_1.value] << 8) | (data[Coe.bp1_0.value])
        otp = self.__convert_signed(otp, 15)
        self.k['bp1'] = self.__calc_k('bp1', otp)
        
        otp = (data[Coe.b11_1.value] << 8) | (data[Coe.b11_0.value])
        otp = self.__convert_signed(otp, 15)
        self.k['b11'] = self.__calc_k('b11', otp)
        
        otp = (data[Coe.bp2_1.value] << 8) | (data[Coe.bp2_0.value])
        otp = self.__convert_signed(otp, 15)
        self.k['bp2'] = self.__calc_k('bp2', otp)
        
        otp = (data[Coe.b12_1.value] << 8) | (data[Coe.b12_0.value])
        otp = self.__convert_signed(otp, 15)
        self.k['b12'] = self.__calc_k('b12', otp)
        
        otp = (data[Coe.b21_1.value] << 8) | (data[Coe.b21_0.value])
        otp = self.__convert_signed(otp, 15)
        self.k['b21'] = self.__calc_k('b21', otp)
        
        otp = (data[Coe.bp3_1.value] << 8) | (data[Coe.bp3_0.value])
        otp = self.__convert_signed(otp, 15)
        self.k['bp3'] = self.__calc_k('bp3', otp)
        
        self.k['tr'] = 25.0 * 256.0

    def __set_powermode(self, mode):
        """
        Parameters
        ----------
        mode : int
        """
        if SMBUS:
            data = self.bus.read_i2c_block_data(self.config['address'], REG_CTRL_MEAS, CTRL_MEAS_LENGTH)
            len = CTRL_MEAS_LENGTH
        else:
            len, data = self.pi.i2c_read_i2c_block_data(self.qmp6988, REG_CTRL_MEAS, CTRL_MEAS_LENGTH)
        if (len == CTRL_MEAS_LENGTH):
            value = data[0] & 0xFC
            
            value |= mode & 0x03
            if SMBUS:
                data = self.bus.write_i2c_block_data(self.config['address'], REG_CTRL_MEAS, [value])
            else:
                self.pi.i2c_write_i2c_block_data(self.qmp6988, REG_CTRL_MEAS, [value])
            time.sleep(0.02)

    def __set_oversampling(self, mode, sampling):
        """
        Parameters
        ----------
        mode : string
        sampling : int
        """
        if (mode == 'temperature'):
            offset = 5
            mask   = 0x1F
        elif (mode == 'pressure'):
            offset = 2
            mask   = 0xE3
        else:
            return
        
        if SMBUS:
            data = self.bus.read_i2c_block_data(self.config['address'], REG_CTRL_MEAS, CTRL_MEAS_LENGTH)
            len = CTRL_MEAS_LENGTH
        else:
            len, data = self.pi.i2c_read_i2c_block_data(self.qmp6988, REG_CTRL_MEAS, CTRL_MEAS_LENGTH)
        if (len == CTRL_MEAS_LENGTH):
            value = data[0] & mask
            
            value |= (sampling & 0x07) << offset
            if SMBUS:
                data = self.bus.write_i2c_block_data(self.config['address'], REG_CTRL_MEAS, [value])
            else:
                self.pi.i2c_write_i2c_block_data(self.qmp6988, REG_CTRL_MEAS, [value])
            time.sleep(0.02)

    def __set_filter(self, filter):
        """
        IIR filter
        
        Parameters
        ----------
        filter : int
            IIR filter
        """
        value = filter & 0x07
        if SMBUS:
            data = self.bus.write_i2c_block_data(self.config['address'], REG_IIR_CNT, [value])
        else:
            self.pi.i2c_write_i2c_block_data(self.qmp6988, REG_IIR_CNT, [value])
        time.sleep(0.02)

    def __convert_signed(self, value, signed_bit):
        """
        bit unsigned int int

        Parameters
        ----------
        value : int
        signed_bit : int

        Returns
        -------
        result : int
        """
        if (value >= (1 << signed_bit)):
            value -= (1 << (signed_bit + 1))
        
        return value

    def __convert_temperature(self):
        """
        QMP6988
        
        Returns
        -------
        temperature : float
            [℃]．
        """
        self.k['tr'] = self.k['a0'] + \
                       (self.k['a1'] * self.k['dt']) + \
                       (self.k['a2'] * (self.k['dt'] ** 2))
        
        temperature = self.k['tr'] / 256.0
        
        return temperature

    def __convert_pressure(self):
        """
        QMP6988
        
        Returns
        -------
        pressure : float
            [hPa]．
        """
        self.k['pr'] = self.k['b00'] + \
                       (self.k['bt1'] * self.k['tr']) + \
                       (self.k['bp1'] * self.k['dp']) + \
                       (self.k['b11'] * self.k['dp'] * self.k['tr']) + \
                       (self.k['bt2'] * (self.k['tr'] ** 2)) + \
                       (self.k['bp2'] * (self.k['dp'] ** 2)) + \
                       (self.k['b12'] * self.k['dp'] * (self.k['tr'] ** 2)) + \
                       (self.k['b21'] * (self.k['dp'] ** 2) * self.k['tr']) + \
                       (self.k['bp3'] * (self.k['dp'] ** 3))

        pressure = self.k['pr'] / 100.0

        return pressure

    def read(self):
        """
        QMP6988
        
        Returns
        -------
        value : dictionary
            {'temperature': , 'pressure': }．
        """
        #self.__pre_process()
    
        if SMBUS:
            if DEBUG:
                print('Attempt to read raw data')
            data = self.bus.read_i2c_block_data(self.config['address'], REG_DATA, DATA_LENGTH)
            #data = self.bus.read_i2c_block_data(0, 0xF7, 6)
            len = DATA_LENGTH
            if DEBUG:
                print('Read raw data')
        else:
            len, data = self.pi.i2c_read_i2c_block_data(self.qmp6988, REG_DATA, DATA_LENGTH)
        
        self.__post_process()
        
        if (len == DATA_LENGTH):
            self.k['dt'] = ((data[Data.TEMP_TXD2.value] << 16) | \
                            (data[Data.TEMP_TXD1.value] << 8) | \
                            (data[Data.TEMP_TXD0.value])) - SUBTRACTOR
            
            self.k['dp'] = ((data[Data.PRESS_TXD2.value] << 16) | \
                            (data[Data.PRESS_TXD1.value] << 8) | \
                            (data[Data.PRESS_TXD0.value])) - SUBTRACTOR

            if (self.config['temperature'] != Oversampling.SKIP.value):
                temperature = self.__convert_temperature()
            else:
                temperature = False
            
            if (self.config['pressure'] != Oversampling.SKIP.value):
                pressure = self.__convert_pressure()
            else:
                pressure = False
        else:
            temperature = False
            pressure    = False
        
        value = {'temperature': temperature, \
                 'pressure': pressure}
        
        return value
