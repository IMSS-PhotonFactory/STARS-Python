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
    def __init__(self, numberOfStarsServer=1, numberOfDeviceServer=1, useConfigFile=True, useLogOutput=True):
        self._parser = None
        self._error = ''
        defaultConfigFileName=''
        self._optdict = {}
        self._optdict['numberOfStarsServer']  = numberOfStarsServer;
        self._optdict['numberOfDeviceServer'] = numberOfDeviceServer;
        self._optdict['useConfig']            = useConfigFile;
        if(os.path.isfile('./config.cfg')):
            defaultConfigFileName='./config.cfg';
        self._optdict['defaultConfigFileName']= defaultConfigFileName;
        self._optdict['useLogOutput']         = useLogOutput;
        self._optdict['useDebugLevel']        = False;
        self._optdict['useLogOutputLevel']    = False;

    def parse_args(self):
        if(self._parser is None):
            self._error = 'Parser undefined';
            return(Namespace({}))
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
        #if(version is not None):
        pparser.add_argument('--nodename', dest='StarsNodeName', help='Enter the Starsnode name of the device.')
        pparser.add_argument('--version'    , action='version', version='%(prog)s '+str(version))
        pparser.add_argument('-d', '--debug', action='store_true', default=False, help='debug mode if this flag is set (default: False)')
        pparser.add_argument('-rawenable', action = 'store_true', default = False, dest = 'sendrawcommand', help = 'Used to send commands directly to the device.(default: False)')        
        pparser.add_argument('-limitstatusenable', action = 'store_true', default = False, dest = 'flg_limitstatus_enable', help = 'Set flg To use Limit status.') 
        pparser.add_argument('--configfile', default=None, dest = 'Config', help = 'Enter the name of the configuration file to use.')

        pparser.add_argument('--devIP', dest='devipadd', help='Change IP address for device.')
        pparser.add_argument('--devPort', dest='devport', help='Change port-Number for device.')

        pparser.add_argument('--pcheckoff', action='store_false', default=True, dest = 'paracheckoff', help='Used to check parameter before command sending to device.(default: False)' )

        usage = 'Usage: NodeName [-h] [-d, --debug] [--version] [-limitstatusenable] [-rawenable]'


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
    configfilename = None
    if(os.path.isfile('config1.cfg')):
        configfilename = 'config.cfg'

    # Parse Arguments
    optIO=PyStarsUtilArgParser(numberOfDeviceServer=1)
    parser=optIO.generate_baseparser(prog='PROG1',version=1.0)
    parser.add_argument('args', nargs='*', help='Command line arguments.')
    args=parser.parse_args()
    print(args.args)
    debug=args.debug
    starsNodeName = optIO.get(args.StarsNodeName,starsNodeName)

    # Fix StarsNodename
    # Read configfile if detected
    configfilename  = optIO.get(args.Config,configfilename)
#    print('          point-S20:  configfilename=' + str(configfilename) + '\n') # for making sure 20220411
    if(configfilename is not None):
        cfgIO= pystarsutilconfig.PyStarsUtilConfig(configfilename,debug)
        if(cfgIO.gethandle() is None):
            exit
        if(not optIO.has_value(args.StarsNodeName)):
            starsNodeName = cfgIO.get('', 'StarsNodeName', starsNodeName)
        debug           = cfgIO.get(starsNodeName, 'Debug'          , debug, bool)
        starsServerHost = cfgIO.get(starsNodeName, 'StarsServerHost', starsServerHost)
        starsServerPort = cfgIO.get(starsNodeName, 'StarsServerPort', starsServerPort, int)
        deviceHost      = cfgIO.get(starsNodeName, 'DeviceHost'     , deviceHost)
        devicePort      = cfgIO.get(starsNodeName, 'DevicePort'     , devicePort, int)


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
