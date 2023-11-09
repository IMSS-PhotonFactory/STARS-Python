#!/usr/bin/python3

"""
   Serial Interface
    Description: Simple Serial Interface library.
    History:
        1.0    2021-04-27 Takashi Kosuge
        1.1    2022-08-03 Takashi Kosuge added compatibility with nportserv.py. Some methods came from the library.
"""
# Define: program info
__author__ = 'Takashi Kosuge'
__version__ = '1.1'
__date__ = '2022-08-03'
__license__ = 'KEK'

import serial
import re
import configparser


class PfiPySerial():
    """Class PfiPySerial
        Excample:
            import pfipyserial
            rs = pfipyserial.PfiPySerial("sereal.cfg")
    """
    DEFAULT_DELIMITER = "\n"
    DEFAULT_TIMEOUT = 3

    def __init__(self, fname="serial.cfg"):
        """Initialize the pfipyserial with config file name.
        """
        cfgall = configparser.ConfigParser()
        cfgall.read(fname)
        cfg = cfgall['serial']
        rs = {}
        self.rdl = {}
        rs['port']      = cfg['Device']
        rs['baudrate']  = 9600
        rs['bytesize']  = serial.EIGHTBITS
        rs['parity']    = serial.PARITY_NONE
        rs['stopbits']  = serial.STOPBITS_ONE
        rs['xonxoff']   = False
        rs['rtscts']    = False
        rs['dsrdtr']    = False
        self.initialtimeout = PfiPySerial.DEFAULT_TIMEOUT
        rs['timeout']   = self.initialtimeout
        #str buffer for readline
        self.rdlbuf = ""
        self.recvdelimiter = PfiPySerial.DEFAULT_DELIMITER
        self.senddelimiter = PfiPySerial.DEFAULT_DELIMITER
        self.error =""
        self.debug = False

        if 'Speed' in cfg:
            rs['baudrate'] = int(cfg['Speed'])
        if 'Data' in cfg:
            bp = int(cfg['Data']) - 5
            if bp >= 0 and bp <= 3:
                rs['bytesize'] = (serial.FIVEBITS, serial.SIXBITS, serial.SEVENBITS, serial.EIGHTBITS)[bp]
        if 'Parity' in cfg:
            if re.match('ODD', cfg['Parity'], re.IGNORECASE):
                rs['parity'] = serial.PARITY_ODD
            elif re.match('EVEN', cfg['Parity'], re.IGNORECASE):
                rs['parity'] = serial.PARITY_EVEN
            elif re.match('MARK', cfg['Parity'], re.IGNORECASE):
                rs['parity'] = serial.PARITY_MARK
            elif re.match('SPACE', cfg['Parity'], re.IGNORECASE):
                rs['parity'] = serial.PARITY_SPACE
        if 'Stop' in cfg:
            bp = int( float(cfg['Stop']) * 2 ) - 2
            if bp >= 0 and bp <= 2:
                rs['stopbits'] = (serial.STOPBITS_ONE, serial.STOPBITS_ONE_POINT_FIVE, serial.STOPBITS_TWO)[bp]
        if 'XonXoff' in cfg:
            if re.match('(YES|TRUE)', cfg['XonXoff'], re.IGNORECASE):
                rs['xonxoff'] = True
        if 'RtsCts' in cfg:
            if re.match('(YES|TRUE)', cfg['RtsCts'], re.IGNORECASE):
                rs['rtscts'] = True
        if 'DsrDtr' in cfg:
            if re.match('(YES|TRUE)', cfg['DsrDtr'], re.IGNORECASE):
                rs['dsrdtr'] = True
        if 'Timeout' in cfg:
            rs['timeout'] = int(cfg['Timeout'])
            self.initialtimeout = rs['timeout']

        self.tty = serial.Serial(**rs)

    def setdebug(self, b):
        """Set true to the argument b, print debug info to stdout.
        """
        if(b == True):
            self.debug = b
        else:
            self.debug = False
        return(True)

    def gettimeout(self):
        """Return the default read timeout
        """
        return self.tty.timeout

    def settimeout(self, timeout=None):
        """Set the default read timeout seconds.
               if set None, reset to the default value DEFAULT_TIMEOUT.
        """
        if timeout is None:
            self.tty.timeout = self.initialtimeout
        elif timeout<0:
            self.error="timeout value {} error. [timeout>=0]".format(timeout)
            return False
        return True

    def getrecvdelimiter(self):
        """Return the default read delimiter string.
        """
        return(self.recvdelimiter)

    def setrecvdelimiter(self, delimiter=None):
        """Set default read delimiter string.
               if set '' as delimiter, it acts like direct read.
                or set None, reset to the default value DEFAULT_DELIMITER.
        """
        if delimiter is None:
#            self.recvdelimiter = nportserv.DEFAULT_DELIMITER
            self.recvdelimiter = PfiPySerial.DEFAULT_DELIMITER
        else:
            self.recvdelimiter = delimiter
        return True

    def getsenddelimiter(self):
        """Return the default send delimiter string.
        """
        return(self.senddelimiter)

    def setsenddelimiter(self, delimiter=None):
        """Set default delimiter string which automatically added to send string.
               if set '' as delimiter, it acts like direct write.
                or set None, reset to the default value DEFAULT_DELIMITER.
        """
        if delimiter is None:
#            self.senddelimiter = nportserv.DEFAULT_DELIMITER
            self.senddelimiter = PfiPySerial.DEFAULT_DELIMITER
        else:
            self.senddelimiter = delimiter
        return True

    def setdelimiter(self, delimiter=None):
        """Set both default recv and send delimiter string.
              if set '' as delimiter, it acts like direct read and write.
                 or set None, reset to the default value DEFAULT_DELIMITER.
        """
        self.setrecvdelimiter(delimiter)
        self.setsenddelimiter(delimiter)
        return True

    def writeb(self, buf):
        """Write to serial port in binary mode.
           ** Not recommended for compatibility with nportserv.py **
        """
        self._debugprint("[writeb] {}".format(buf))
        try:
            self.tty.write(buf)
        except:
            self.error = "Serial out error."
            return False
        return True

    def readb(self):
        """Read from serial port in binary mode.
            ** Not recommended for compatibility with nportserv.py **
        """
        buf = self.tty.read()
        self._debugprint("[readb] {}".format(buf))
        return buf

    def write(self, buf):
        """Write to serial port.
            ** Not recommended for compatibility with nportserv.py **
        """
        self._debugprint("[write] {}".format(buf))
        self.tty.write(buf.encode('utf-8'))

    def read(self):
        """Read from serial port.
            ** Not recommended for compatibility with nportserv.py **
        """
        buf = self.tty.read().decode('utf-8')
        self._debugprint("[read] {}".format(buf))
        return buf

    def readline(self):
        """Read from serial port with delimiter.
            ** Not recommended for compatibility with nportserv.py **
        """
        while True:
            mtchd = re.match('[^{0:}]+{0:}'.format(self.recvdelimiter), self.rdlbuf)
            if mtchd != None:
                self.rdlbuf = re.sub(mtchd.group(), '', self.rdlbuf, 1)
                return mtchd.group().replace(self.recvdelimiter, '')
            buf = self.read()
            if len(buf) == 0:
                return(buf)
            self.rdlbuf += buf

    def send(self, smsg, delimiter=None):
        """Send message
             Return False for send error,
               or else return True.
             Set the arguments - delimieter if change temporarily the default value.
        """
        if delimiter is None:
            delimiter = self.senddelimiter
        return self.write(smsg + delimiter)

    def receive(self, timeout='', delimiter=None, exceptionret = None):
        """Receieve message
             Return received data.
             Set the arguments - timeout, delimieter if change temporarily the default value.
             Value exceptonret is dummy for compativility.
        """
        if delimiter is None:
            delimiter = self.recvdelimiter
        if delimiter == '':
            return self.read()
        else:
            return self.readline()

    def connect(self, force=False):
        """Dummy for compatibility with nportserv.py.
             Returns True.
        """
        return True

    def disconnect(self, force=True):
        """Dummy for compatibility with nportserv.py.
             Returns True.
        """
        return True

    def gethandle(self):
        """Return serial handle, None value means no socket.
        """
        return self.tty

    def getlasterrortext(self):
        """Return the last error string.
        """
        return(self.error)

    def isconnected(self):
        """Dummy for compatibility with nportserv.py.
             Returns True.
        """
        return True

    def printinfo(self):
        """Print the instance variables info, Just use for debug.
        """
        print("port     = {}".format(self.tty.port))
        print("baudrate = {}".format(self.tty.baudrate))
        print("bytesize = {}".format(self.tty.bytesize))
        print("parity   = {}".format(self.tty.parity))
        print("stopbits = {}".format(self.tty.stopbits))
        print("xonxoff  = {}".format(self.tty.xonxoff))
        print("rtscts   = {}".format(self.tty.rtscts))
        print("dsrdtr   = {}".format(self.tty.dsrdtr))
        print("timeout  = {}".format(self.tty.timeout))

    def _debugprint(self, msg):
        if self.debug:
            print(msg)


if __name__ == '__main__':
    import threading
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('cfgfile', help = "Config file")
    #parser.add_argument('host', nargs = '?', help = "hostname or IP address") #nargs:'*','?','+',number
    #parser.add_argument('-t', '--timeout', type = int, default = 3, help = "Ping timeout")
    args = parser.parse_args()
    sr = PfiPySerial(args.cfgfile)
    def rdproc():
        while True:
            print(sr.receive(), end='')
    th_rs_read = threading.Thread(target=rdproc)
    print(sr.printinfo())
    th_rs_read.start()
    while True:
        buf = sys.stdin.readline()
        sr.send(buf)
