#! /usr/bin/python3

import sys
import time
import os
from argparse import ArgumentParser
from pystarsutil import pystarsutilconfig

#----------------------------------------------------------------
# Class Python utility Config
#----------------------------------------------------------------
class PyStarsUtilArgParser():
    """ Class PyStarsUtilArgParser:
    """

    #----------------------------------------------------------------
    # Error functions
    #----------------------------------------------------------------
    def getlasterrortext(self):
        """ getlasterrortext: Return the last error message text.

              Returns:
                (string) the last error message text.
        """
        return(self._error)

    #----------------------------------------------------------------
    # debug functions
    #----------------------------------------------------------------
    def setdebug(self, b):
        """ setdebug: debug option.

              Parameters:
                b -- (bool) set True to print debug infomation text to stdout.
        """
        if(b == True):
            self._debug = b
        else:
            self._debug = False
        return

    def _debugprint(self,msg):
        if(self._debug == True):
            try:
                ct=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
                sys.stdout.write(ct+' '+msg)
            except Exception as e:
                return
        return

    #----------------------------------------------------------------
    # Initialize:
    #----------------------------------------------------------------
#    def __init__(self, numberOfStarsServer=1, numberOfDeviceServer=1, useConfigFile=True, useLogOutput=True):
    def __init__(self,useConfigFile=True):
#
        self._parser = None
        self._error = ''
        defaultConfigFileName=''
        self._optdict = {}

    def parse_args(self):
        if(self._parser is None):
            self._error = 'Parser undefined';
            return(parser.Namespace({}))

        parser=self._parser
        args=parser.parse_args()
        return(args)

    def has_value(self, targetvalue):
        if(targetvalue is None):
            return False
        return(True)

    def get(self, targetvalue, defaultvalue):
        if(targetvalue is None):
            return defaultvalue
        return(targetvalue)

    def set_baseproperty(self,name,value):
        if(name in self._optdict):
            self._optdict[name]  = value
            return(True)
        return(False)

    def generate_baseparser(self,prog=None,version=None,usage=None,description=None,epilog=None):
        pparser = ArgumentParser(add_help=False)
        if(version is not None):
            pparser.add_argument('--version'    , action='version', version='%(prog)s '+str(version))
        pparser.add_argument('-d', '--debug', action='store_true', default=False, help='debug mode if this flag is set (default: False)')
        pparser.add_argument('-i', action='store_true', dest='FlgInvert', help='Invert sign of output.')
        pparser.add_argument('--nodename', dest='nodename', help='Setting device name.')
        pparser.add_argument('--avgcount', dest='averagecount', help='Specifying the number of times to calculate the average.')
        pparser.add_argument('--digitnum', dest='digitalnum', help='Definition of number of digits after the decimal point.')
#
        pparser.add_argument('--devIP', dest='devipadd', help='Change IP address for device.')
        pparser.add_argument('--devPort', dest='devport', help='Change port-Number for device.')
#
        usage = 'Usage: NodeName [-h] [-d, --debug] [-i] [--version] [--avgcount "number"] [--digitnum "digitalnumber"] [--devIP "IPaddress"] [--devPort "Port Number]'


        parser = ArgumentParser(prog=prog,usage=usage,description=description,epilog=epilog,parents=[pparser])

        self._parser = parser
        return(self._parser)


###############################################################################
# Main: Test
###############################################################################
if __name__ == '__main__':
    import sys
    import pystarsutilconfig

    #vDefault values
    debug=False
    starsNodeName = 'termtest'
    starsServerHost = '127.0.0.1'
    starsServerPort = 1001
    deviceHost = '127.0.0.2'
    devicePort = 4001

    # Parse Arguments
    optIO=PyStarsUtilArgParser(numberOfDeviceServer=1)
    parser=optIO.generate_baseparser(prog='PROG1',version=1.0)
    parser.add_argument('args', nargs='*', help='Command line arguments.')
    args=parser.parse_args()
    print(args.args)
    debug=args.debug
    starsNodeName = optIO.get(args.StarsNodeName,starsNodeName)



    # Fix optional parameters
    starsServerHost = optIO.get(args.StarsServerHost,starsServerHost)
    starsServerPort = optIO.get(args.StarsServerPort,starsServerPort)
    deviceHost      = optIO.get(args.DeviceHost,deviceHost)
    devicePort      = optIO.get(args.DevicePort,devicePort)

    if(debug==True):
        print("starsNodeName#"+str(starsNodeName)+"#")
        print("starsServerHost#"+str(starsServerHost)+"#")
        print("starsServerPort#"+str(starsServerPort)+"#")
        print("deviceHost#"+str(deviceHost)+"#")
        print("devicePort#"+str(devicePort)+"#")
