from abc import ABC, abstractmethod # Import for abstract method

# --- Definition of control bits constants --- #
# Command
cmdNoop = 0x0
cmdWriteInputN = 0x1
cmdUpdateDACN = 0x2
cmdWriteInputNUpdateN = 0x3
cmdPowerDownDAC = 0x4
cmdLDACMask = 0x5
cmdReset = 0x6
cmdInternalReferSetup = 0x7
cmdDaisyChainEnable = 0x8
cmdReadbackEnable = 0x9

# LDAC mode
ldacPwndnNone = 0x0
ldacPwndn1k = 0x1
ldacPwndn100k = 0x2
ldacPwndn3state = 0x3

# DAC address
def addrDAC(chan):
    return 0x1 << (chan)

addrAllDAC = 0xf

# Configuration of DAC
MAX_CHANNEL = 4

# MASKs
MASK_CMD = 0xf
MASK_ADDR = 0xf
MASK_DATA = 0xffff

MASK_PWNDN = 0x3


class adidac24(ABC): 
    # class for 24-bit command DACs
    # ---- DB23 down-to DB0 ----
    # CCCCAAAA DDDDDDDD DDDDDDDD
    
    # reference voltage
    @property
    def vRef(self):
        return self._vRef
    @vRef.setter
    def vRef(self, value):
        self._vRef = value
    
    # gain
    @property
    def gain(self):
        return self._gain
    @gain.setter
    def gain(self, value):
        if value >= 1.5:
            self._gain = 2
        else:
            self._gain = 1
    
    @property
    def reg(self):
        return self._reg.regstate
    
    def __init__(self, gain=1, vref=2.5):
        self._gain = gain
        self._vRef = vref
        self._reg = self.state()
        
    
    # --- Define Commands Control Procedures ---

    # cmdWriteInputN = 0x1
    # Write to input register CHAN
    def writeInputN(self, chan, data):
        cmd =  cmdWriteInputN
        addr = addrDAC(chan)
        self.updateReg(cmd, addr, data)
        self._ldacActive()
        return

    # Write to several input registers controlled by addr
    def writeInputMask(self, addr, data):
        # 0001dcba DDDDDDDD DDDDDDDD
        # dcba, e.g. 1010 means control DAC D & B simultaneously
 
        cmd =  cmdWriteInputN
        self.updateReg(cmd, addr, data)
        self._ldacActive()
        return
    
    # cmdUpdateDACN = 0x2
    def updateDACN(self, chan, data):
        cmd = cmdUpdateDACN
        addr = addrDAC(chan)
        self.updateReg(cmd, addr, data)
        return
    
    # cmdWriteInputNUpdateN = 0x3
    def writeInputNUpdateN(self, chan, data):
        cmd = cmdWriteInputNUpdateN
        addr = addrDAC(chan)
        self.updateReg(cmd, addr, data)
        return

    # cmdPowerDownDAC = 0x4
    def powerDown(self, addr, mode):
        # 0100xxxx xxxxxxxx ddccbbaa
        # CMD NO - RELATION PWNDnMODE
        cmd =  cmdPowerDownDAC 
        pwnMode = mode & MASK_PWNDN
        data = 0
        for ia in range(0,MAX_CHANNEL-1):
            if ((addr>>ia) & 0x1) == 1 :
                data += pwnMode << (ia * 2)
                
        self.updateReg(cmd, addr, data)
        
    # cmdLDACMask = 0x5
    def LDACMask(self, addr):
        # 0101xxxx xxxxxxxx xxxxDDDD
        # CMD NO - RELATION ----MASK
        cmd =  cmdLDACMask 
        data = addr & MASK_ADDR
        self.updateReg(cmd, addr, data)
        return
    
    # cmdReset = 0x6
    # cmdInternalReferSetup = 0x7
    def internalReferSetup(self, value):
        # 0111xxxx xxxxxxxx xxxxxxxD
        # CMD NO - RELATION xxxxxxxYES
        cmd =  cmdInternalReferSetup 
        data = value & 0x1
        self.updateReg(cmd, 0, data)
        return
    
    # cmdDaisyChainEnable = 0x8
    def daisyChainEnable(self, value):
        cmd =  cmdDaisyChainEnable 
        data = value & 0x1
        self.updateReg(cmd, 0, data)
        return

    # cmdReadbackEnable = 0x9
    def readbackEnable(self, value):
        cmd =  cmdReadbackEnable 
        data = value & 0x1
        self.updateReg(cmd, 0, data)
        return
        
    def updateReg(self, cmd, addr, data):
        self._reg.setStateReg(cmd,addr,data)
        self._chipSelect()
        self._chipWrite()
        self._chipRelease()
        return
        
    # PIN control abstract methods that should be XXXX in child class
    # Manipulate pin level according to the circuit and platform
    @abstractmethod
    def _chipSelect(self):
        pass
    @abstractmethod
    def _chipRelease(self):
        pass
    @abstractmethod
    def _chipWrite(self):
        pass
    @abstractmethod
    def _ldacActive(self):
        pass
    
    # subclass to manage the 24-bit communication command
    class state():
        # The state reg is 24-bit in total, where the structure is defined as 
        # CCCCAAAA DDDDDDDD DDDDDDDD
        # CCCC is commandMASK_DATA
        # AAAA is address
        # DD...D are data bits, where the left 12-bit, 14-bit or 16-bit are used

        def __init__(self, cmd=0, addr=0, data=0):
            self.setStateReg(cmd, addr, data)
            
        def setStateReg(self, cmd=0, addr=0, data=0):
            self._cmd = cmd & MASK_CMD
            self._addr = addr & MASK_ADDR
            self._data = data & MASK_DATA
            self.makereg()
            
        @property
        def cmd(self):
            return self._cmd
        @cmd.setter
        def cmd(self, value):
            self._cmd = value & MASK_CMD
            self.makereg()
            
        @property
        def addr(self):
            return self._addr
        @addr.setter
        def addr(self, value):
            self._addr = value & MASK_ADDR
            self.makereg()
            
        @property
        def data(self):
            return self._data
        @data.setter
        def data(self, value):
            self._data = value & MASK_DATA
            self.makereg()

        @property
        def regstate(self):
            return self._regstate
        @regstate.setter
        def regstate(self, value):
            b1 = (value & 0xff0000) >> 16
            b2 = (value & 0xff00) >> 8
            b3 = value & 0xff
            self._regstate = bytes([b1, b2, b3])           

        def makereg(self):
            b1 = (self._cmd << 4) + self._addr
            b2 = ((self._data) & 0xff00) >> 8
            b3 = (self._data) & 0xff
            self._regstate = bytes([b1 , b2, b3])
            
