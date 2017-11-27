#!/usr/bin/env python
"""
Set a resistance on MCP41010 (digital potentiometer), then measure the effect
using MCP3008 (analog-digital converter).
"""

import time
import argparse
import spi

MAX_CHANNELS = 8

def execute(vdd, num_channels, order='down'):
    """
    Cycle digipot output and take measurements off of ADC channels.  Returns
    a list of tuples; one list element per digipot value, and each tuple
    contains the outputs of all measured ADC channels.
    """
    ### use two independent SPI buses, but daisy chaining then is also valid
    adc = spi.SPI(clk=18, cs=25, mosi=24, miso=23, verbose=False)
    digipot = spi.SPI(clk=19, cs=13, mosi=26, miso=None, verbose=False)
    results = []

    ### order refers to the voltage, which is the inverse of the resistance
    if order == 'down':
        indices = range(2**8)
    elif order == 'up':
        indices = range(2**8 - 1, 0, -1)
    elif order == 'downup':
        indices = range(2**8) + range(2**8 - 1, 0, -1)
    elif order == 'updown':
        indices = range(2**8 - 1, 0, -1) + range(2**8)
    else:
        raise Exception("order must be one of: up down downup updown")

    ### iterate over all possible resistance values
    for resist_val in indices:
        ### set resistance on digipot
        set_digipot(digipot, resist_val)

        ### wait to allow voltage transients to subside
        time.sleep(0.01)

        ### get the voltage from the MCP3008 ###############################
        adc_values = get_adc(adc)[0:num_channels]
        results.append(tuple([x * vdd for x in adc_values]))

    return results

def print_results(results, pin_labels):
    """Print outputs as a CSV"""
    output_str = ','.join('%6s' for _ in pin_labels) % pin_labels + "\n"
    for voltages in results:
        output_str += ','.join('%6.2f' for _ in voltages) % voltages + '\n'
    print output_str

def set_digipot(digipot, value):
    """
    Set the value of the output pin on the digipot
    """
    ### set the resistance on the MCP41010
    cmd = int("00010001", 2)
    # make room for resist_val's 8 bits
    cmd <<= 8
    digipot.put(cmd|value, bits=16)

def get_adc(adc):
    """
    Get the value of the output pin on the digipot
    """
    ### get the voltage from the MCP3008 ###############################
    voltages = [0] * MAX_CHANNELS
    for channel_id in range(MAX_CHANNELS):
        # set the start bit, single-ended mode bit, and 3 channel select bits
        cmd = int("11000", 2) | channel_id
        # read 1 null bit, then 10 data bits
        cmd <<= 10 + 1
        value = adc.put_get(cmd, bits=16)
        # mask off everything but the last 10 read bits
        value &= 2**10 - 1
        # convert 10-bit value to a voltage
        voltages[channel_id] = value / 1023.0
    return tuple(voltages)

def setup_and_run():
    """
    CLI interface into the experiment
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--order', type=str, default='down', help="how to scale voltage (up, down, updown, downup)")
    parser.add_argument('--vdd', type=float, default=5.0, help="VDD voltage (default=5.0)")
    parser.add_argument('-c', '--channels', type=int, default=4, help="number of channels to examine (default: 4)")
    args = parser.parse_args()

    results = execute(vdd=args.vdd, num_channels=args.channels, order=args.order)
    print_results(results, pin_labels=('TRIG', 'THRES', 'RESET', 'OUT'))

if __name__ == '__main__':
    setup_and_run()
