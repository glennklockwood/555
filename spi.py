#!/usr/bin/env python
"""
A very simple SPI implementation that allows you to assign arbitrary GPIO pins
to act as SPI wires and put/get data.
"""

import sys
from RPi import GPIO

### Reference counter--once we hit zero, deconfigure GPIO entirely
_CONFIGURATIONS = 0

class SPI(object):
    """
    Configure and maintain a software-implemented SPI connection via Raspberry
    Pi's GPIO interface
    """
    def __init__(self, clk, cs, mosi, miso, verbose=False):
        """Create a simple SPI pin map and configure an initial known state"""
        global _CONFIGURATIONS
        self.clk = clk
        self.cs = cs
        self.mosi = mosi
        self.miso = miso
        if verbose:
            self.verbose = True
        else:
            self.verbose = False
        GPIO.setmode(GPIO.BCM)
        ### sometimes you don't need an input or an output, so they're optional
        if self.mosi:
            GPIO.setup(self.mosi, GPIO.OUT, initial=GPIO.LOW)
        if self.miso:
            GPIO.setup(self.miso, GPIO.IN)
        GPIO.setup(self.clk, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.cs, GPIO.OUT, initial=GPIO.HIGH)
        _CONFIGURATIONS += 1

    def __del__(self):
        """
        Track how many instances of this object are still referenced; when the
        last one is destroyed, shut down the GPIO subsystem.
        """
        global _CONFIGURATIONS
        _CONFIGURATIONS -= 1
        if _CONFIGURATIONS == 0:
            GPIO.cleanup()

    def clk_tick(self):
        """
        Tick the clock pin
        """
        GPIO.output(self.clk, GPIO.HIGH)
        GPIO.output(self.clk, GPIO.LOW)

    def cs_low(self):
        """
        Bring the cable select pin low
        """
        GPIO.output(self.cs, GPIO.LOW)

    def cs_high(self):
        """
        Bring the cable select pin high
        """
        GPIO.output(self.cs, GPIO.HIGH)

    def put(self, data, bits, control_cs=True):
        """
        Send a bit vector of a given length over MOSI
        """
        data_buf = data
        packet = ""
        if control_cs:
            self.cs_low()
        try:
            for _ in range(bits):
                if data_buf & (2**(bits-1)):
                    GPIO.output(self.mosi, GPIO.HIGH)
                    packet += "1"
                else:
                    GPIO.output(self.mosi, GPIO.LOW)
                    packet += "0"
                data_buf <<= 1
                self.clk_tick()
            self._vprint("Sent [%s]" % packet)
        except:
            if control_cs:
                self.cs_high()
            raise

        if control_cs:
            self.cs_high()

    def get(self, bits, control_cs=True):
        """
        Get a bit vector of a given length via MISO
        """
        data_buf = 0x0

        packet = ""
        if control_cs:
            self.cs_low()
        try:
            for _ in range(bits):
                self.clk_tick()
                data_buf <<= 1
                if GPIO.input(self.miso):
                    data_buf |= 0x1
                    packet += "1"
                else:
                    packet += "0"
            self._vprint("Recv [%s]" % packet)
        except:
            if control_cs:
                self.cs_high()
            raise

        if control_cs:
            self.cs_high()
        return data_buf

    def put_get(self, data, bits):
        """
        Put and get bit vectors concurrently
        """
        put_data = data
        get_data = 0x0
        put_packet = ""
        get_packet = ""
        self.cs_low()
        try:
            for _ in range(bits):
                if put_data & (2**(bits-1)):
                    GPIO.output(self.mosi, GPIO.HIGH)
                    put_packet += "1"
                else:
                    GPIO.output(self.mosi, GPIO.LOW)
                    put_packet += "0"
                put_data <<= 1
                self.clk_tick()
                get_data <<= 1
                if GPIO.input(self.miso) == GPIO.HIGH:
                    get_data |= 0x1
                    get_packet += "1"
                else:
                    get_packet += "0"
            self._vprint("Sent [%s]" % put_packet)
            self._vprint("Recv [%s]" % get_packet)
        except:
            self.cs_high()
            raise

        self.cs_high()
        return get_data


    def _vprint(self, msg):
        """
        Print messages only when debugging is enabled
        """
        if self.verbose:
            sys.stderr.write(msg + "\n")
