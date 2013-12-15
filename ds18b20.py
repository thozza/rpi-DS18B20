# -*- coding: utf-8 -*-
#
# ds18b20.py - simple module for working with DS18B20 sensor using 'w1-gpio'
#              and 'w1-therm' kernel modules and 'sysfs'.
# Copyright 2013 Tomas Hozza <thozza@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# Authors:
# Tomas Hozza <thozza@gmail.com>

import os
import glob
import subprocess


def check_required_kmods():
    """
    Checks if required kernel modules are loaded, if not, raises
    RuntimeError Exception. Required modules are:
    - w1-gpio
    - w1-therm
    """
    if (subprocess.call("lsmod | grep w1_gpio", shell=True) != 0):
        raise RuntimeError("\"w1-gpio\" kernel module is not loaded!")
    if (subprocess.call("lsmod | grep w1_therm", shell=True) != 0):
        raise RuntimeError("\"w1-therm\" kernel module is not loaded!")


def load_required_kmods():
    """
    Loads necessary kernel modules:
    - w1-gpio
    - w1-therm
    """
    if os.getuid() != 0:
        raise RuntimeError("Need to root to load kernel modules")
    if (subprocess.call("modprobe w1-gpio") != 0):
        raise RuntimeError("Failed to load \"w1-gpio\" kernel module!")
    if (subprocess.call("modprobe w1-therm") != 0):
        raise RuntimeError("Failed to load \"w1-therm\" kernel module!")


class sensor(object):
    sysfs_base_path = "/sys/bus/w1/devices/"

    def __init__(self):
        check_required_kmods()
        # TODO: should add function for getting the list of devices and
        #       then accept the path in the constructor
        devices = glob.glob("/sys/devices/w1_bus_master1/28-*/w1_slave")
        if not devices:
            raise RuntimeError(
                "No DS18B20 device found in '/sys/devices/w1_bus_master1'!")
        # use the first one
        self.device_path = devices[0]

    def read_temperature(self):
        """
        Tries to read the temperature from the sensor via the 'sysfs' 5x.
        if it fails, it raises RuntimeError.
        The returned temperature is in Celzius degrees
        """
        #try to get the temperature 5x
        for tries in range(5):
            with open(self.device_path, "r") as device_file:
                lines = device_file.readlines()
                # check CRC - the line looks as follows
                # 62 01 4b 46 7f ff 0e 10 03 : crc=03 YES
                if lines[0].decode("utf-8").strip()[-3:] != "YES":
                    continue
                # get the temperature - the line looks as follows
                # 61 01 4b 46 7f ff 0f 10 02 t=22062
                tmp_str = lines[1].decode("utf-8").strip()[-7:]
                if not tmp_str.startswith("t="):
                    continue
                return float(tmp_str[2:]) / 1000.0

        raise RuntimeError("Failed to read the the temperature successfully!")