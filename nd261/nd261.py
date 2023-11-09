#! /usr/bin/python3
"""
   STARS python program for HEIDENHAIN nd261 Encoder
    Description: Connect to STARS server and commnicate with the device.
    History:
       0.0     Base program written by Yasuko Nagatani
       1.0     ----.--.--   Beta     Hahsimoto Yoshiaki
""" 
## Define: program info
__author__ = 'Hashimoto Yoshiaki'

__version__ = '1.0'


__date__  = '2023-01-18'
__license__ = 'KEK'

#--------------------------------------------------------------
# Class PyStarsDevice ND261

#----------------------------------------------------------------

#from logging.config import _RootLoggerConfiguration

from calendar import month_name

from email.utils import decode_rfc2231

from shutil import register_unpack_format

#
import nportserv
#import pfipyserial


import re

import time
#

import glob
#


class PyStarsDevice_nd261(nportserv.nportserv):
    """ Class PyStarsDevice_xxxx   _xxxx; device name
    """
    ##################################################################
    #                      Device control functions                  #
    ##################################################################
    #    data transfer function    #
    ################################
    ## Device send
    def device_send(self,cmd):
#        print('                      >>>>>    point-A00 device-send ---> PM16C-command = ' + cmd +'\n')
        if(self.isconnected()==False):
            return 'Er: Disconnected'
#        cmd = cmd + '\r\n'                  # temp 20220914
        rt=self.send(cmd)
        if(rt==False):
            return 'Er: ' + dc.getlasterrortext()
        self._deviceCommandLastExecutedTime = time.time()
        return 'Ok:'

    ## Device act
    def device_act(self,cmd,timeout=''):
        rt=self.device_send(cmd)
        if('Er:' in rt):
            return(rt)
        rt=self.device_receive(timeout)
        return rt

    ## Device receive
    def device_receive(self,timeout=''):
        if(timeout==''):
            timeout=self.gettimeout()
        rt=self.receive(timeout)
        if(rt is None):
            return('Er: '+self.error)
        if(rt == ''):
            return('Er: Timeout.')
        return rt

###################################################################
#   command execution procedure
###################################################################

    def getdata(self,avgcount):
        global gb_Debug
        global gb_Flginvert
        global gb_DIGITUM
        _debflg = gb_Debug
        _flginv = gb_Flginvert
        _diginum =gb_DIGITUM
        _avci = int(avgcount)

        rt = 'Ok:'
        _rt = 'Er:'
        _cmds = chr(2)      # ASCII ; STX
        _val = 0

        if(_avci < 1):
            _avci = 1
        _lc = _avci
        for v in range(_lc):
            rt = self.device_act(_cmds)
            if(rt == ''):
                rt = _rt + 'The device does not respond.'
                return(rt)
            elif('Er:' in rt):
                return(rt)
            else:
                try:
                     _rti = float(rt)
                except ValueError:
                    rt = _rt + 'Bad data recieved from the device.'
                    return(rt)
            if(_flginv == True):
                _rti = -1*_rti
            _val = _val + _rti
            if(_debflg == True):
                print('ND261 Value' + str(v) + ' = ' + str(_val) + '\n')
        _vala = float(_val/_avci)
        if(_debflg == True):
            print('ND261  AverageValue(' + str(_val) + '/' + str(_avci) + ' = ' + str(_vala) + '\n')

        digi = '.0' + str(_diginum) +'f'
        rt = format(_vala,digi)
        return(rt)

    def get_commandlastexecutedtime(self):
        return(self._deviceCommandLastExecutedTime)


    ##############################################
    #  constructor      #
    ##############################################

    def __init__(self, deviceHost, devicePost, inthandler=None):
        self._deviceInstance = nportserv.nportserv.__init__(self, deviceHost, devicePost)
        #self.setdelimiter('\r\n')
        self.settimeout(2)
##########################################################################
#                  Define informations for STARSCommand                  #
##########################################################################
    ##################################################################
    def _set_commandlastwaittime(self,t):
        self._deviceCommandLastWaitTime=t;

#----------------------------------------------------------------
# Program nd261.py
#----------------------------------------------------------------
if __name__ == "__main__":
    ##################################################################
    # Import modules
    ##################################################################
    import sys
    import os
    from singlestars import StarsInterface
    from stars import StarsMessage
#    from pystarsutil import pystarsutilconfig, pystarsutilargparser
    from pystarsutil import pystarsutilargparser

    ##################################################################
    # Define program parameters
    ##################################################################
    # Initialize: Global parameters
    gb_ScriptName = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    #ScriptPath = os.path.dirname(os.path.abspath(sys.argv[0]))
    gb_Debug = False
#    gb_NumberOfChannels = 1  # Set default number of channels.
#    gb_MotorNameList = []           # Assumed to be used in the motor name discribed comfig.cfg
#    gb_ChannelNameSeqList = []
#    gb_ChannelNameList = {}
    gb_StarsInstance = None
    gb_DeviceInstance = None
#
    gb_AverageCount = 1
    gb_DIGITUM = 4
    gb_Flginvert = 0
#
#    gb_userconfigfile = True
#    gb_SelectCl = 'Eth'
# for display informations to cliant windows
    gb_devicename = ''
    gb_cliant = ''
# SendRawCommand
#    gb_SRawC = False
# SupportDeviceFlg
#    gb_pm16cx = 'off'
    supportdevice = 'no'
# constant for time control
#    WAIT_MEMWRITE = 40/1000
#    WAIT_HOLD_ON = 100/1000
#    WAIT_HOLD_OFF = 500/1000
#    WAIT_SELECT = 40/1000
#    INTERVAL_STOP = 2000/1000
    INTERVAL_RUN = 100/1000
#    REFRESH_RUN = 500/1000
#    WAIT_BUB = 100/1000
# time interval control
    gb_Interval_Time = INTERVAL_RUN

# Define: Appliction default parameters
    starsServerHost = 'localhost'
    starsNodeName   = 'tdkzplus'
    starsServerPort = 6057
#
    deviceHost = '192.168.11.160'
#    deviceHost = '172.16.0.53' # dummy for debug 20230104
    devicePort = 4001       #7777  #8003
#    devicePort = 7777       # dummy for debug 20230104
#
#################################################################################
#           Function definition       >>>>>>>>>>>>>>>>>>>                       #
#################################################################################

    ##################################################################
    # Define local functions: print
    ##################################################################
    # Define: print function
    #from logging import NOTSET,DEBUG,INFO,WARN,WARNING,ERROR,CRITICAL,FATAL
#    DEBUG = 10
    INFO = 20
    WARN = 30
    def _outputlog(level, mesg, outstderronly=False):
        global gb_ScriptName
        global gb_Debug
        head = gb_ScriptName
        
        if(gb_Debug==False):
            if(level<=INFO):
                return(1)
        if(outstderronly == True):
            if(mesg[-1:] != '\n'):
               mesg=mesg+'\n'
            sys.stderr.write(mesg)
        else:
            if(mesg[-1:] != '\n'):
               mesg=mesg+'\n'
            sys.stderr.write(mesg)
            #logger.log(level,'['+ head + '] ' + mesg)
        return(1)

    ##################################################################
    # Callback functions:
    ##################################################################
    ## Device socket handler: DETECT
    def device_sockhandler(sock):
        global gb_StarsInstance
        st = gb_StarsInstance
        global gb_DeviceInstance
        dc = gb_DeviceInstance

        destsendstr="Device_detected %s.\n" %(st.nodename)
        _outputlog(WARN, destsendstr)
        rt=st.send('System _Msg '+destsendstr)

        rt = dc.isconnected()
        while rt==True:
            rt = dc.receive(0.01)
            if(rt is None):
                dc.disconnect()
                destsendstr="Device_disconnected %s.\n" %(st.nodename)
                _outputlog(WARN, destsendstr)
                rt=st.send('System _Msg '+destsendstr)
                st.terminateMainloop()
            elif(rt != ''):
                destsendstr="Device_read#%s#\n" %(rt)
                continue
            rt = dc.isconnected()
            break
        return(rt)


    ## STARS interval handler:
    def interval():
        global gb_StarsInstance
        st = gb_StarsInstance
        global gb_DeviceInstance
        dc = gb_DeviceInstance
#        global gb_pm16cx
#        pm16cx = gb_pm16cx
        global gb_Debug
        debugmode = gb_Debug
#
        dc.setdebug('False')
        st.setdebug('False')
#
        # Check device connectection
        if(dc.isconnected() == False):
            destsendstr="Terminate STARS %s. [Device disconnection]\n" %(st.nodename)
            _outputlog(WARN, destsendstr)
            rt=st.send('System _Msg '+destsendstr)
            st.terminateMainloop()
            return

#
        dc.setdebug(debugmode)
        st.setdebug(debugmode)
#        
        return

    ## STARS socket handler
    def handler(allmess,sock):
        global gb_ScriptName
        global gb_StarsInstance
        global gb_DeviceInstance
        global gb_Debug
#       for nd261
        global gb_AverageCount
#
        global gb_devicename
        global gb_cliant
#
        dc = gb_DeviceInstance
        st = gb_StarsInstance
#

        destsendstr='';
        if allmess == '':
            st.terminateMainloop()
            return
        elif(allmess.parameters == ''):
            message = allmess.command
        else:
            message = allmess.command + ' ' + allmess.parameters
        command   = allmess.command
        parameter = allmess.parameters
        parameters = []

        gb_devicename = allmess.nodeto
        gb_cliant = allmess.nodefrom
#
        if(allmess.parameters != ''):
            parameters = allmess.parameters.split(" ")
        if(gb_Debug==True):
            print("STARS ALL MESSAGE "+allmess)
            print("STARS FROMNODE "+allmess.nodefrom)
            print("STARS TONODE "+allmess.nodeto)
            print("STARS COMMAND "+allmess.command)
            print("STARS ALL PARAMETER "+allmess.parameters)
        _outputlog(INFO, 'STARS Recv[' +st.nodename + "]:"+allmess)
        topnode = st.nodename
        channelname = ''
        rt = ''


######################################################################
##    handler process  ; currentmotor = _currentmotor
######################################################################
#
        if(allmess.nodeto.startswith(st.nodename)):
            if(message.startswith('@')):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + 'Er: Invalid command. '
                _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
                rt=st.send(destsendstr)
                return
            elif(message.startswith('_')):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + 'Er: Invalid command. '
                _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
                rt=st.send(destsendstr)
                return
            elif(message == 'getversion'):
                rt = gb_ScriptName + ' Ver.'+__version__+', '+__date__+', '+__author__
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(message == 'getversionno'):
                rt = __version__
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Ver.' + rt
            elif(message == 'hello'):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Nice to meet you.'
            elif(message == 'help'):
                rt = 'hello, help, getversion, getversionno, GetValue, SendAsC, terminate'
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif(command == 'help' and len(parameters) == 1):
                _cmd = parameters[0]
                if(_cmd == 'GetValue'):
                    rt = ' Get measurements from device.'
                elif(_cmd == 'getversion'):
                    rt = 'Return this program version.'
                elif(_cmd == 'getversionno'):
                    rt = 'Return this program version number.'
                elif(_cmd == 'hello'):
                    rt = 'The client returns that hello nice to meet you.'
                elif(_cmd == 'terminate'):
                    rt = 'The client processing terminates.'
                elif(_cmd == 'SendAsC'):
                    rt = 'Send ASCII code to device. Available codes are STX, DC1, DC3 and ENQ.'
                else:
                    rt = 'ER: Bad parameter.'
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + rt
            elif(message == 'GetValue'):
                _avcount = gb_AverageCount
                rt = dc.getdata(_avcount)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
#
            elif(message == 'terminate'):
                st.terminateMainloop()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Ok:'
#

###########
            elif( command == 'SendAsC' and parameter != ''):
                if('STX' == parameter):
                    _asi = int(2)
                    _ascom = chr(_asi)
                    rt = dc.device_act(_ascom)
                elif('ENQ' == parameter):
                    _asi = int(5)
                    _ascom = chr(_asi)
                    rt = dc.device_act(_ascom)
                elif('DC3' == parameter):
                    _asi = int(19)
                    _ascom = chr(_asi)
                    rt = dc.device_send(_ascom)
                elif('DC1' == parameter):
                    _asi = int(17)
                    _ascom = chr(_asi)
                    rt = dc.device_send(_ascom)
                else:
                    rt = 'Input ASCII code is not supported.'
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ; ' + rt
###########
            else:
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad command or parameters.'
        else:
            if(message.startswith('@')):
                return
            elif(message.startswith('_')):
                return
            else:
                destsendstr = st.nodename + '>' + allmess.nodefrom+' @' + message + ' Er: Bad node.'
            if(destsendstr != ''):
                _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
                rt=st.send(destsendstr)
            else:
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad command or parameters.'
        if(destsendstr != ''):
            _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
            rt=st.send(destsendstr)
            if(rt==False):
                st.terminateMainloop()
        return


#################################################################################
#                               <<<<<<<<<<<<<<<<<<    Function definition       #
#################################################################################

 	##################################################################    
    # Define program arguments
    ##################################################################
    optIO=pystarsutilargparser.PyStarsUtilArgParser()
    parser=optIO.generate_baseparser(prog=gb_ScriptName,version=__version__)
    ##################################################################
    # Parse program arguments
    ##################################################################
    args=parser.parse_args()
    gb_Debug=args.debug
    gb_Flginvert = args.FlgInvert

    if(gb_Debug==True):
        sys.stdout.write(str(args)+'\n')

    starsNodeName = optIO.get(args.nodename,None)
    if( starsNodeName == 'nd261'):
        supportdevice = 'yes'
    if( supportdevice == 'no'):
        _rt = 'Sorry, the input model is not supported. Please check the model.'
        sys.stdout.write(_rt +'\n')
        exit(1)


#
    avgc = optIO.get(args.averagecount,None)
    if(avgc is not None):
        gb_AverageCount = avgc
    dinm = optIO.get(args.digitalnum,None)
    if(dinm is not None):
        gb_DIGITUM = dinm
#
    dvip = optIO.get(args.devipadd,None)
    if(dvip is not None):
        deviceHost = dvip
    dvpt = optIO.get(args.devport,None)
    if(dvpt is not None):
        try:
            dvpti = int(dvpt)
        except ValueError:
            sys.stdout.write('bad port number' + '\n')
            exit(1)
        devicePort = dvpti
#


    if(gb_Debug==True):
        sys.stdout.write("starsNodeName#"+str(starsNodeName)+"#"+'\n')
        sys.stdout.write("starsServerHost#"+str(starsServerHost)+"#"+'\n')
        sys.stdout.write("starsServerPort#"+str(starsServerPort)+"#"+'\n')
        sys.stdout.write("deviceHost#"+str(deviceHost)+"#"+'\n')
        sys.stdout.write("devicePort#"+str(devicePort)+"#"+'\n')
#        sys.stdout.write("numberOfChannels#"+str(gb_NumberOfChannels)+"#"+'\n')
#        sys.stdout.write("channelNameList#"+str(gb_ChannelNameList)+"#"+'\n')

    ##################################################################
    # Main process: Start
    ##################################################################

    #Create device instance with devserver:devport 
    dc=PyStarsDevice_nd261(deviceHost, devicePort)
    gb_DeviceInstance=dc
    #print(dc._deviceFUNCCommand)
    #exit(1)

    #Set properties for device instance
    dc.setdebug(gb_Debug)
    if(gb_Debug == True):
        gb_DeviceInstance.printinfo()

    #Connect to device
    rt = dc.connect()
    if(rt==False):
        sys.stdout.write(dc.getlasterrortext()+'\n')
        exit(1)

    #Create Stars instance
    st  = StarsInterface(starsNodeName, starsServerHost, '', starsServerPort)
    gb_StarsInstance = st

    #Set properties for Stars instance
    st.setdebug(gb_Debug)

    rt = st.setdefaultreceivetimeout(3)
    if(rt==False):
        sys.stdout.write(st.getlasterrortext()+'\n')
        exit(1)

    #Connect to Stars
    rt=st.connect()
    if(rt==False):
        sys.stdout.write(st.error+'\n')
        exit(1)

    #Send device info
    time.sleep(3)

    #Add callback handler
    rt=st.addcallback(handler)
    if(rt==False):
        sys.stdout.write(st.getlasterrortext()+'\n')
        exit(1)
    rt=st.addcallback(device_sockhandler,dc.gethandle(),'DETECT')
    if(rt==False):
        sys.stdout.write(st.getlasterrortext()+'\n')
        exit(1)


    print('\n' + '  <<<<<< main loop start >>>>>>  ' + '\n')       #for check into mainloop


    rt=st.Mainloop(interval,gb_Interval_Time)
    if(rt==False):
        sys.stdout.write(st.error+'\n')
        exit(1)

    #Device close
    #*** sleep for callback terminate wait
    time.sleep(1)
    dc.disconnect()
    st.removecallback()
    st.disconnect()
    exit(0)
