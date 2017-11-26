#!/usr/bin/env python
"""
Set a resistance on MCP41010 (digital potentiometer), then measure the effect
using MCP3008 (analog-digital converter).
"""

import time
import spi

def execute(vdd, num_channels):
    """
    Cycle digipot output and take measurements off of ADC channels.  Returns
    a list of tuples; one list element per digipot value, and each tuple
    contains the outputs of all measured ADC channels.
    """
    ### use two independent SPI buses, but daisy chaining then is also valid
    adc = spi.SPI(clk=18, cs=25, mosi=24, miso=23, verbose=False)
    digipot = spi.SPI(clk=19, cs=13, mosi=26, miso=None, verbose=False)

    ### iterate over all possible resistance values (8 bits = 256 values)
    results = []
    for resist_val in range(2**8):
        ### set the resistance on the MCP41010
        cmd = int("00010001", 2)
        # make room for resist_val's 8 bits
        cmd <<= 8
        digipot.put(cmd|resist_val, bits=16)

        ### wait to allow voltage transients to subside
        time.sleep(0.01)

        ### get the voltage from the MCP3008 ###############################
        voltages = [0] * num_channels
        for channel_id in range(num_channels):
            # set the start bit, single-ended mode bit, and 3 channel select bits
            cmd = int("11000", 2) | channel_id
            # read 1 null bit, then 10 data bits
            cmd <<= 10 + 1
            value = adc.put_get(cmd, bits=16)
            # mask off everything but the last 10 read bits
            value &= 2**10 - 1
            # convert 10-bit value to a voltage
            voltages[channel_id] = vdd * value / 1023.0
        results.append(tuple(voltages))
    return results

def print_results(results, pin_labels):
    """Print outputs as a CSV"""
    output_str = ','.join('%6s' for _ in pin_labels) % pin_labels + "\n"
    for voltages in results:
        output_str += ','.join('%6.2f' for _ in voltages) % voltages + '\n'
    print output_str

if __name__ == '__main__':
    print_results(
        execute(vdd=5.0, num_channels=4),
        pin_labels=('TRIG', 'THRES', 'RESET', 'OUT'))
