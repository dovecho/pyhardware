import spidev
import RPi.GPIO as GPIO
import sys, getopt
import time

from adiNanoDAC import *
        
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 1000000

pin_SYNC1 = 7
pin_LDAC1 = 6
pin_RESET1 = 24

pin_SYNC0 = 8
pin_LDAC0 = 5
pin_RESET0 = 23


class AD5684R(adidac24):
    
    def __init__(self, cs, ldac, reset, gain=1, vref=2.5):
        adidac24.__init__(self, gain, vref)
        self._cs = cs
        self._ldac = ldac
        self._reset = reset
        GPIO.setup(cs, GPIO.OUT)
        GPIO.output(cs, 1)
        GPIO.setup(ldac, GPIO.OUT)
        GPIO.output(ldac, 1)
        GPIO.setup(reset, GPIO.OUT)
        GPIO.output(reset, 1)

    def _chipSelect(self):
        GPIO.output(self._cs, 0)
        return
    
    def _chipRelease(self):
        GPIO.output(self._cs, 1)
        return
    
    def _chipWrite(self):
        print(self.reg)
        resp = spi.xfer2(self.reg)
        return
    
    def _ldacActive(self):
        GPIO.output(self._ldac, 0)
        GPIO.output(self._ldac, 1)
        return

def main(argv):
    
    aa0 = AD5684R(pin_SYNC0, pin_LDAC0, pin_RESET0)
    aa0.gain = 2
    aa1 = AD5684R(pin_SYNC1, pin_LDAC1, pin_RESET1)
    aa1.gain = 1
    
    try:
        aa0.writeInputN(0, 100)
        time.sleep(0.1)
        aa1.writeInputMask(0xf, 600)
        
    except KeyboardInterrupt:
        spi.close()

    spi.close()

if __name__ == "__main__":
    main(sys.argv[1:])
