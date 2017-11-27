#!/usr/bin/env python
"""
Tool for getting and setting the value on an MCP41010 digital potentiometer.
This is handy for initializing the resistance value after shuffling wires around
to ensure that the state of the MCP41010 is known at the start of a test.
"""

import time
import argparse
import spi
import experiment

def set_get_digipot():
    parser = argparse.ArgumentParser()
    parser.add_argument('--vdd', type=float, default=5.0, help="VDD voltage (default=5.0)")
    parser.add_argument("value", nargs="?", default=None, type=int, help="value to set digipot (0-1023)")
    args = parser.parse_args()

    adc = spi.SPI(clk=18, cs=25, mosi=24, miso=23, verbose=False)
    digipot = spi.SPI(clk=19, cs=13, mosi=26, miso=None, verbose=False)

    if args.value is not None:
        experiment.set_digipot(digipot, args.value)
        time.sleep(0.01)
        print "Digipot set to %d Ohms" % (10000.0 * args.value / 1023.0)

    values = experiment.get_adc(adc)
    for channel, value in enumerate(values):
        print "Channel %d: %.2f" % (channel, value * args.vdd)

if __name__ == "__main__":
    set_get_digipot()
