#! /usr/bin/python3
"""
   STARS python program for PM16C-04/04X made by TSUJICON
    Description: Connect to STARS server and commnicate with the device.
    History:
       0.0     Base program written by Yasuko Nagatani
       1.0     2022.12.13   Beta     Hahsimoto Yoshiaki
       1.1     2022.12.19   Debug mode support
       1.11    2022.12.22   Fix title comment
       1.2     2023.03.17   brush-up
""" 
## Define: program info
__author__ = 'Hashimoto Yoshiaki'

__version__ = '1.2'


__date__  = '2023-03-17'
__license__ = 'KEK'

#--------------------------------------------------------------
# Class PyStarsDevice Tsujicon PM16C

#----------------------------------------------------------------

#from logging.config import _RootLoggerConfiguration

from calendar import month_name

from email.utils import decode_rfc2231

from shutil import register_unpack_format

import nportserv
import re

import time
#

import glob
#


class PyStarsDevice_pm16c(nportserv.nportserv):
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
            return 'Er : Disconnected'      # " " added for IsBusy
#        cmd = cmd + '\r\n'                  # temp 20220914
        rt=self.send(cmd)
        if(rt==False):
            return 'Er : ' + dc.getlasterrortext()  # " " added for IsBusy
        self._deviceCommandLastExecutedTime = time.time()
        return 'Ok:'

    ## Device act
    def device_act(self,cmd,timeout=''):
        rt=self.device_send(cmd)
        if('Er :' in rt):                   # " " added for IsBusy
            return(rt)
        rt=self.device_receive(timeout)
        return rt

    ## Device receive
    def device_receive(self,timeout=''):
        if(timeout==''):
            timeout=self.gettimeout()
        rt=self.receive(timeout)
        if(rt is None):
            return('Er : '+self.error)      # " " added for IsBusy
        if(rt == ''):
            return('Er : Timeout.')         # " " added for IsBusy
        return rt

    #################################
    #     device reset functions    #
    #################################
    ## Device reset  20220413
    def device_reset(self):
        _cmd = ':*CLS'              # IEEE488.2 standerd command
        self.device_send(_cmd)
        _cmd = ':SYST:ERR?'         # IEEE488.2 SCPI command
        rt = self.device_act(_cmd)
        if('No error' not in rt):
            return rt
        _cmd = ':*RST'
        self.device_send(_cmd)
        _cmd = ':SYST:ERR?'         # IEEE488.2 SCPI command
        rt = self.device_act(_cmd)
        if('No error' not in rt):
            return rt 
        _cmd = ':FORM:ELEM READ,UNIT,CHAN'  # IEEE488.2 SCPI command
        self.device_send(_cmd)      
        return 'OK'

        return 'OK'

    ############################################
    #    Command table manegement functions    #
    ############################################

################ 20220826
    def is_commanddefined(self,model= 'off', category='Controller', starscommand=''):
        _mf = model
        _ctf = category
        _tf = 0
        if(starscommand in self._deviceComSTARSCommand):
            return(_tf)
        elif( _ctf == 'Controller'):
            if(starscommand in self._deviceCTLSTARSCommand):
                _tf = 1
                return(_tf)
            elif((_mf=='on') and (starscommand in self._deviceXCTLSTARSCommand)):
                _tf = 2
                return(_tf)
        elif( _ctf == 'Motor'):
            if(starscommand in self._deviceMOTSTARSCommand):
                _tf = 3
                return(_tf)
            elif((_mf == 'on') and (starscommand in self._deviceXMOTSTARSCommand)):
                _tf = 4
                return(_tf)
        return(False)

    def get_commandlist(self,model= 'off',category='Controller' ):
        _mf = model
        _ctf = category
        clist = []
        clist0 = []
        clist1 = []
        clist2 = []
        clist3 = []
        clist4 = []

        clist0 = self._deviceComSTARSCommand.keys()
        clist1 = self._deviceCTLSTARSCommand.keys()
        clist2 = self._deviceMOTSTARSCommand.keys()
        clist3 = self._deviceXCTLSTARSCommand.keys()
        clist4 = self._deviceXMOTSTARSCommand.keys()

        for ck0 in clist0:
            _target = self._deviceComSTARSCommand[ck0]['Target']
            if( _target == 'Common'):
                clist.append(ck0)
        if( _ctf == 'Controller'):
            for ck1 in clist1:
                _target = self._deviceCTLSTARSCommand[ck1]['Target']
                if( _target == 'Controller'):
                    clist.append(ck1)
            if( _mf == 'on'):
                for ck3 in clist3:
                    _target = self._deviceXCTLSTARSCommand[ck3]['Target']
                    if( _target == 'Controller'):
                        clist.append(ck3)
        else:                               # ; _ctf == 'Motor'
            for ck2 in clist2:
                _target = self._deviceMOTSTARSCommand[ck2]['Target']
                if( _target == 'Motor'):
                    clist.append(ck2)
            if( _mf == 'on'):
                for ck4 in clist4:
                    _target = self._deviceXMOTSTARSCommand[ck4]['Target']
                    if( _target == 'Motor'):
                        clist.append(ck4)
        return(clist)


    def get_commandhelp(self, tblflg, starscommand):
        rt='-'
        if(tblflg == 0):
            rt=self._deviceComSTARSCommand[starscommand]['help']
        elif(tblflg == 1):
            rt=self._deviceCTLSTARSCommand[starscommand]['help']
        elif(tblflg == 2):
            rt=self._deviceXCTLSTARSCommand[starscommand]['help']
        elif(tblflg == 3):
            rt=self._deviceMOTSTARSCommand[starscommand]['help']
        elif(tblflg == 4):
            rt=self._deviceXMOTSTARSCommand[starscommand]['help']
        return(rt)

###################################################################
#   command execution procedure
###################################################################

    def get_commandlastexecutedtime(self):
        return(self._deviceCommandLastExecutedTime)

    def get_motorspeed_n4x(self,mf):
        _pm16cx = mf
        if( _pm16cx == 'off'):
            return(self._MotorSpeed)
        else:
            return('Ng: Set number from 1 to 5000000 in PM16C-04X.')

    def get_AccRate(self,mf):
        _pm16cx = mf
        if(_pm16cx == 'on'):
            return(self._AccelarationRate)
        else:
            return(self._MotorSpeedRate)

    def Ctl_GetFunction(self,fm='off'):
        global gb_Flg_remote
        global gb_MotorNameList
        global gb_MotorBusy
        global gb_devicename
        global gb_cliant
#
        _remotelocal = gb_Flg_remote
        _motlist = gb_MotorNameList
        _motbsy = gb_MotorBusy
        _fm = fm                    # flushdatatome -> 'on'
        _device = gb_devicename
        _cliant = gb_cliant
        _ckR = ''
#
        if( '.' in _device):
            _devtmp = _device.split('.',1)
            _device = _devtmp[0]
#
        _rts = self.Ctl_GetFunctionStatus()
        if( 'Er:' in _rts ):
            return(_rts)
        _rts_t = int(_rts,16)
        _result = _rts_t & 0x0800
        _resultx_t = format(_result,'X')
        _resultx = _resultx_t.zfill(4)
#
        if( _resultx == '0800'):
            _ckR = '1'
        else:
            _ckR = '0'

        if((_fm == 'on' ) or (_remotelocal != _ckR)):
            _destsendstr = 'System _ChangedFunction' + ' ' + _ckR 
            st.send(_destsendstr)
            gb_Flg_remote = _ckR
            for v in range(0,16):
                self.Motor_GetCancelBacklash(v)
                _motname = _motlist[v]
                _rt = self.Motor_GetValue(v)
                _destsendstr =  str(_device) + '.' + str(_motname)  + '>System _ChangedValue' + ' ' + str(_rt)
                st.send(_destsendstr)
                _destsendstr = str(_device) + '.' + str(_motname) + '>' + str(_cliant) + ' ' + '_ChangedValue' + ' ' + str(_rt)
                st.send(_destsendstr)
                _destsendstr = str(_cliant)  + '>System _ChangedIsBusy' + ' ' + str(_rt)
                st.send(_destsendstr)
                _destsendstr = str(_device) + '.' + str(_motname) + '>' + str(_cliant) + ' ' + '_ChangedIsBusy' + ' ' + _motbsy[v]
                st.send(_destsendstr)
#
        rt = _ckR
        return(rt)

    def Ctl_GetFunctionStatus(self):
        _cmd = 'S6'
        _cksts = "R\w\w\w\w"
        _dsts = self.device_act(_cmd)
        _ckr = re.match(_cksts,_dsts)
        _rt = ''
        if( _ckr is None):
            _rt = 'Er: Could not get function.'
            return(_rt)
        _rt = _dsts.lstrip('R')
        return(_rt)

    def Ctl_IsBusy(self,ch=''):        # temp 20220915   _rt =1 ; Busy  ,  _rt = 0 ; not busy
        global gb_Is_busyflg_A
        global gb_Is_busyflg_B
        global gb_Is_busyflg_C
        global gb_Is_busyflg_D

        _Flg_Busy = [gb_Is_busyflg_A,gb_Is_busyflg_B,gb_Is_busyflg_C,gb_Is_busyflg_D]
        _ch = ch

        _rt = '0'
        if(_ch == ''):
            if((_Flg_Busy[0] != 'nE') and (_Flg_Busy[1] != 'nE') and (_Flg_Busy[2] != 'nE') and (_Flg_Busy[3] != 'nE')):
                _rt = '1'
        elif(_ch == 'ALL'):
            if(_Flg_Busy[0] != 'nE'):
                _rt = ' A:1 ,'
            else:
                _rt = ' A:0 ,'
            if(_Flg_Busy[1] != 'nE'):
                _rt = _rt + ' B:1 ,'
            else:
                _rt = _rt + ' B:0 ,'
            if(_Flg_Busy[2] != 'nE'):
                _rt = _rt + ' C:1 ,'
            else:
                _rt = _rt + ' C:0 ,'
            if(_Flg_Busy[3] != 'nE'):
                _rt = _rt + ' D:1'
            else:
                _rt = _rt + ' D:0'
        elif((_ch == 'A') and (_Flg_Busy[0] != 'nE') ):
            _rt = '1'
        elif((_ch == 'B') and (_Flg_Busy[1] != 'nE') ):
            _rt = '1'
        elif((_ch == 'C') and (_Flg_Busy[2] != 'nE') ):
            _rt = '1'
        elif((_ch == 'D') and (_Flg_Busy[3] != 'nE') ):
            _rt = '1'
        return(_rt)

    def Ctl_Select(self,ch='',mnox=''):
        global gb_Is_busyflg_A
        global gb_Is_busyflg_B
        global gb_Is_busyflg_C
        global gb_Is_busyflg_D
        global gb_pm16cx
        
        _pm16cx = gb_pm16cx
        _ch = ch.upper()
        _motornumber = mnox
        _cmd =''
        _cmd0 =''
        _bchno = 'not'
        _cksts = 'R\w\w\w\w'
        _rt = 'Er:'
        rt = ''

        if( _ch == 'A'):
            _cmd0 = 'S11'
        elif( _ch == 'B'):
            _cmd0 = 'S12'
        elif( _ch == 'C'):
            _cmd0 = 'S15'
        elif( _ch == 'D'):
            _cmd0 = 'S16'
        else:
            rt = _rt + 'Bad channel'
            return(rt)
        _ckctlb = self.Ctl_IsBusy(_ch)
        if(_ckctlb == '1'):
            rt = _rt + ' Busy'        
            return(rt)

        _ckmotb = self.Motor_IsBusy(_motornumber)
        if(_ckmotb == '1'):
            rt = _rt + ' Busy'
            return(rt)
        _cmd = 'S10'
        _dsts = self.device_act(_cmd)
        _ckr = re.match(_cksts,_dsts)
        if(_ckr is None):
            rt = _rt + ' Could not get setting motor number. 1'
            return(rt)
        _dstschi = _dsts.lstrip('R')
        _tplsts = tuple(_dstschi)
        if(_ch == 'A'):
            if(_motornumber == _tplsts[1]):
                _bchno = 'B'
            elif(_motornumber == _tplsts[2]):
                _bchno = 'C'
            elif(_motornumber == _tplsts[3]):
                _bchno = 'D'
        elif(_ch == 'B'):
            if(_motornumber == _tplsts[0]):
                _bchno = 'A'
            elif(_motornumber == _tplsts[2]):
                _bchno = 'C'
            elif(_motornumber == _tplsts[3]):
                _bchno = 'D'
        elif(_ch == 'C'):
            if(_motornumber == _tplsts[0]):
                _bchno = 'A'
            elif(_motornumber == _tplsts[1]):
                _bchno = 'B'
            elif(_motornumber == _tplsts[3]):
                _bchno = 'D'
        elif(_ch == 'D'):
            if(_motornumber == _tplsts[0]):
                _bchno = 'A'
            elif(_motornumber == _tplsts[1]):
                _bchno = 'B'
            elif(_motornumber == _tplsts[2]):
                _bchno = 'C'
        else:
            rt = _rt + ' Bad channel'
            return(rt)
        if(_bchno != 'not' and _pm16cx == 'off'):
            rt = _rt + ' Already selected on other channel.'
            return(rt)
        _cmd = _cmd0 + _motornumber
        self.device_send(_cmd)
        _cmd = 'S10'
        _dsts2 = self.device_act(_cmd)
        _ckr = re.match(_cksts,_dsts2)
        if(_ckr is None):
            rt = _rt + ' Could not get setting motor number. 2'
            return(rt)
        _dstschi2 = _dsts2.lstrip('R')
        _tplsts2 = tuple(_dstschi2)
        if(_ch == 'A'):
            if(_motornumber == _tplsts2[0]):
                rt = 'Setting Ok:'
            else:
                rt = _rt + 'Could not select.'
        elif(_ch == 'B'):
            if(_motornumber == _tplsts2[1]):
                rt = 'Setting Ok:'
            else:
                rt = _rt + 'Could not select.'
        elif(_ch == 'C'):
            if(_motornumber == _tplsts2[2]):
                rt = 'Setting Ok:'
            else:
                rt = _rt + 'Could not select.'
        elif(_ch == 'D'):
            if(_motornumber == _tplsts2[3]):
                rt = 'Setting Ok:'
            else:
                rt = _rt + ' Could not select.'
        else:
            rt = _rt + ' Could not select.'
        if( (_pm16cx == 'on') and (rt == 'Setting_Ok')):
            if(_ch == 'A'):
                if(((_bchno == 'B') and (_tplsts[0] == _tplsts2[1])) or ((_bchno == 'C') and (_tplsts[0] == _tplsts2[2])) or ((_bchno == 'D') and (_tplsts[0] == _tplsts2[3]))):
                    rt = 'Ok:'
            elif(_ch == 'B'):
                if(((_bchno == 'A') and (_tplsts[1] == _tplsts2[0])) or ((_bchno == 'C') and (_tplsts[1] == _tplsts2[2])) or ((_bchno == 'D') and (_tplsts[1] == _tplsts2[3]))):
                    rt = 'Ok:'
            elif(_ch == 'C'):
                if(((_bchno == 'A') and (_tplsts[2] == _tplsts2[0])) or ((_bchno == 'B') and (_tplsts[2] == _tplsts2[1])) or ((_bchno == 'D') and (_tplsts[2] == _tplsts2[3]))):
                    rt = 'Ok:'
            elif(_ch == 'D'):
                if(((_bchno == 'A') and (_tplsts[3] == _tplsts2[0])) or ((_bchno == 'B') and (_tplsts[3] == _tplsts2[1])) or ((_bchno == 'C') and (_tplsts[3] == _tplsts2[2]))):
                    rt = 'Ok:'
            else:
                rt = _rt + ' setting error.'
        _tplsts2A = str(int(_tplsts2[0],16))
        _tplsts2B = str(int(_tplsts2[1],16))
        _tplsts2C = str(int(_tplsts2[2],16))
        _tplsts2D = str(int(_tplsts2[3],16)) 
#        rt = rt + ' The setting are A:' + _tplsts2[0] + ', B:' + _tplsts2[1] + ', C:' + _tplsts2[2] + ', D:' + _tplsts2[3] + '.'
        rt = rt + ' The setting is [ A:' + _tplsts2A + ', B:' + _tplsts2B + ', C:' + _tplsts2C + ', D:' + _tplsts2D + ' ].'
        return(rt)

    def Ctl_Speed(self,sf=''):
        global gb_pm16cx
        _speedflg = sf
        _pm16cx = gb_pm16cx
        _rt = 'Er: This command is not supported on the device.'
        if(_pm16cx == 'on'):
            _rt = self.CtlX_SetSpeed(_speedflg)
            return(_rt)
        _ckd = self.Ctl_GetFunction()
        if( (_ckd == '0' ) or ('Er:' in _ckd)):
            _rt = 'Offline.'
            return(_rt)
        _ckb0 = self.Ctl_IsBusy(ch = 'A')
        _ckb1 = self.Ctl_IsBusy(ch = 'B')
        _ckb2 = self.Ctl_IsBusy(ch = 'C')
        _ckb3 = self.Ctl_IsBusy(ch = 'D')
        if((_ckb0 == '1') or (_ckb1 == '1') or (_ckb2 == '1') or (_ckb3 == '1')):
            _rt = 'Busy'
            return(_rt)
        if(_speedflg == '1'):             # SpeedLow
            _cmd ='S34'
            self.device_send(_cmd)
            return('Ok:')
        if(_speedflg == '2'):             # SpeedMiddle
            _cmd ='S35'
            self.device_send(_cmd)
            return('Ok:')
        if(_speedflg == '3'):             # SpeedHigh
            _cmd ='S36'
            self.device_send(_cmd)
            return('Ok:')
        return(_rt)

    def CtlX_SetSpeed(self,mf):
        _speedflg = mf
        rt ='Ok:'
        if(_speedflg == '3'):
            _speedflg = 'H'
        elif(_speedflg == '2'):
            _speedflg = 'M'
        else:
            _speedflg = 'L'

#        _rol = self.rolbusy()
#        if('Er:' in _rol):
#            rt = _rol
        for v in range(16):
            _mnox = format(v,'X')
            _rsts = self.MotorX_SetSpeed(_mnox,_speedflg)
            if('Er:' in _rsts):
                rt = _rsts
                break
        return(rt)


    def Ctl_Stop(self,ch='',mode=''):
        global gb_pm16cx
        _ch = ch.upper()
        _mode = mode
        _pm16cx = gb_pm16cx
        _cmd = ''
        _cmd2 = '40'
        if(_pm16cx == 'on'):
            _rt = self.CtlX_Stop(_ch,_mode)
            return(_rt)
        if(_mode == '1'):
            _cmd2 = '80'
        if(_ch == 'A'):
            _cmd = 'S30' + _cmd2
            self.device_send(_cmd)
        elif(_ch == 'B'):
            _cmd = 'S31' + _cmd2
            self.device_send(_cmd)
        elif(_ch == 'C'):
            _cmd = 'S38' + _cmd2
            self.device_send(_cmd)
        elif(_ch == 'D'):
            _cmd = 'S39' + _cmd2
            self.device_send(_cmd)
        else:
            _cmd = 'S30' + _cmd2
            self.device_send(_cmd)
            _cmd = 'S31' + _cmd2
            self.device_send(_cmd)
            _cmd = 'S38' + _cmd2
            self.device_send(_cmd)
            _cmd = 'S39' + _cmd2
            self.device_send(_cmd)
        return('Ok:')

    def CtlX_Stop(self,ch='',mode=''):
        _ch = ch.upper()
        _mode = mode
        _cmd = ''
        _cmd2 = '40'
        if(_mode == '1'):
            _cmd2 = '80'
        if(_ch == 'A'):
            _cmd = 'S30' + _cmd2
            self.device_send(_cmd)
        elif(_ch == 'B'):
            _cmd = 'S31' + _cmd2
            self.device_send(_cmd)
        elif(_ch == 'C'):
            _cmd = 'S38' + _cmd2
            self.device_send(_cmd)
        elif(_ch == 'D'):
            _cmd = 'S39' + _cmd2
            self.device_send(_cmd)
        elif(_mode == '1'):
            _cmd = 'AESTP'
            self.device_send(_cmd)
        else:
            _cmd = 'ASSTP'
            self.device_send(_cmd)
        return('Ok:')

    def Ctl_SetHold(self,ch='',hld=''):
        _ch =ch.upper()
        _hld = hld
        _cmd = ''
        _rt = 'ER:'
        rt = 'Ok:'
        if(_ch == 'A'):
            _cmd = 'S30'
        elif(_ch == 'B'):
            _cmd = 'S31'
        elif(_ch == 'C'):
            _cmd = 'S38'
        elif(_ch == 'D'):
            _cmd ='S39'
        else:
            rt = _rt + ' Bad channel.'
            return(rt)
        
        _rolb = self.rolbusy(_ch)
        if('Er:' in _rolb):
            rt = _rolb
            return(rt)

        if((_hld == '1') or (_hld == 'ON')):
            _cmd = _cmd + '19'
            self.device_send(_cmd)
            time.sleep(WAIT_HOLD_ON)
        elif((_hld == '0') or (_hld == 'OFF')):
            _cmd = _cmd + '18'
            self.device_send(_cmd)
            time.sleep(WAIT_HOLD_OFF)
        else:
            rt = _rt + ' Bad parameter.'
        return(rt)

    def Ctl_Standby(self):
        _rt ='Ok:'
        _dsts = self.Ctl_GetFunction()
        if( _dsts == '0'):
            _rt = 'Offline'
            return(_rt)
        _cmd = 'S3016'
        self.device_send(_cmd)
        return(_rt)

    def Ctl_SyncRun(self):
        _rt ='Ok:'
        _dsts = self.Ctl_GetFunction()
        if( _dsts == '0'):
            _rt = 'Offline'
            return(_rt)
        _cmd = 'S3017'
        self.device_send(_cmd)
        return(_rt)

    def Ctl_GetSelected(self,chs):
        _cksts = 'R\w\w\w\w'
        _rt = 'Er:'
        _ch = chs.upper()

        _cmd = 'S10'
        _dsts2 = self.device_act(_cmd)
        _ckr = re.match(_cksts,_dsts2)
        if(_ckr is None):
            _rt = _rt + 'Could not get setting motor number. 2'
        else:
            _dstschi2 = _dsts2.lstrip('R')
            _tplsts2 = tuple(_dstschi2)
            if(_ch == 'A'):
                _rt = _tplsts2[0]
            elif(_ch == 'B'):
                _rt = _tplsts2[1]
            elif(_ch == 'C'):
                _rt = _tplsts2[2]
            elif(_ch == 'D'):
                _rt = _tplsts2[3]
            elif(_ch == 'ALL'):
                _rt = 'A:' + _tplsts2[0] + ', B:' + _tplsts2[1] + ', C:' + _tplsts2[2] + ', D:' + _tplsts2[3]
            else:
                _rt = _rt + 'Bad channel select.'
        if(_ch == 'INTERNAL'):
            _rt = _tplsts2
        return(_rt)

    def Ctl_getstatus(self,ch):
        global gb_Is_busyflg_A
        global gb_Is_busyflg_B
        global gb_Is_busyflg_C
        global gb_Is_busyflg_D
        Flg_Busy_A = gb_Is_busyflg_A
        Flg_Busy_B = gb_Is_busyflg_B
        Flg_Busy_C = gb_Is_busyflg_C
        Flg_Busy_D = gb_Is_busyflg_D
        _ch =ch
        _rt = self.pm16c_getstatus(_ch)
#        _rt = int(_rtt,base=16)
#        if( _ch == 'A'):
#            if( Flg_Busy_A == 'nE'):
#                _flgdj = 0
#            else:
#                _flgdj = int(Flg_Busy_A,base=16)
#        elif( _ch == 'B'):
#            if( Flg_Busy_B == 'nE'):
#                _flgdj = 0
#            else:
#                _flgdj = int(Flg_Busy_B,base=16)
#        elif( _ch == 'C'):
#            if( Flg_Busy_C == 'nE'):
#                _flgdj = 0
#            else:
#                _flgdj = int(Flg_Busy_C,base=16)
#        elif( _ch == 'D'):
#            if( Flg_Busy_D == 'nE'):
#                _flgdj = 0
#            else:
#                _flgdj = int(Flg_Busy_D,base=16)
#        else:
#            rt = 'Er: Bad channel.'
#            return(rt)
#        rt = _rt | _flgdj   # The processing is the same as the pearl processing, but it is necessary to confirm whether this processing is correct.
        _ckdC = format(_rt,'X')
        rt = _ckdC.zfill(2)
        return(rt)

    def Ctl_SetValue(self,ch,val,fn):
        _ch = ch
        _sd = val
        _mode = fn
        rt = 'Ok:'
#        _rol = self.Ctl_GetFunction()
        _sts = self.rolbusy(_ch)
        if('Er:' in _sts):
            rt = _sts
            return(rt)
        _cchx = self.Ctl_GetSelected(_ch)
        if('Er:' in _cchx):
            rt = _cchx
            return(rt)
        _cchi = int(_cchx,16)
        _rt = self.pm16c_SetValue(_ch,_sd,_cchi,_mode)
        rt = _rt
        return(rt)

    def Ctl_GetValue(self,ch):
        global gb_pm16cx
        _ch = ch

        _pm16cx = gb_pm16cx
        _cksts6 = 'R\w\w\w\w\w\w'
        _cmd = ''
        _rt = 'Er:'
        rt = ''

        if(_pm16cx == 'on'):
            rt = self.CtlX_GetValue(_ch)
            return(rt)
        if(_ch == 'A'):
            _cmd = 'S20'
        elif(_ch == 'B'):
            _cmd = 'S22'
        elif(_ch == 'C'):
            _cmd = 'S24'
        elif(_ch == 'D'):
            _cmd = 'S26'
        else:
            rt = _rt + ' Bad Channel.'
            return(rt)
##
        _dsts = self.device_act(_cmd)
        _ckr = re.match(_cksts6,_dsts)
        if(_ckr is None):
            rt = _rt + ' Bad read value.'
            return(rt)
        _dstschi = _dsts.lstrip('R')
        _dstsht = int(_dstschi,16)
        _dckk = _dstsht & 0x800000
        _dckkx = format(_dckk,'X')
        _dckr = _dckkx.zfill(6)
        if(_dckr != '000000'):
            _strd = (_dstsht ^ 0xffffff )*(-1)-1
            _dstsht = format(_strd,'X')
            _dstsht = int(_dstsht,16)
        _dstsh = str(_dstsht)
#        rt = _dstsh.zfill(6)
        rt = _dstsh
        return(rt)


    def CtlX_GetValue(self,ch):
        _ch =ch
        _fc ='0'
        _rt = 'Er:'
        rt = ''

        if((_ch != 'A') and (_ch != 'B') and (_ch != 'C') and (_ch != 'D')):
            rt = _rt + ' Bad channel.'
            return(rt)
        _mnosx = self.Ctl_GetSelected(_ch)
        _mnoi = int(_mnosx,16)
        _rsts = self.pm16cX_GetValue(_mnoi,_fc)
        rt = _rsts
        return(rt)

    def Ctl_Scan(self,ch,md):
        _chs = ch
        _mode = md
        rt = 'Ok:'
        _rlb  = self.rolbusy(_chs)
        if( 'Er:' in _rlb):
            rt = _rlb
            return(rt)
        _mnox = self.Ctl_GetSelected(_chs)
        if('Er:' in _mnox):
            rt = _mnox
        else:
            _rsts = self.pm16c_Scan(_chs,_mnox,_mode)
            rt =_rsts
        return(rt)

    def CtlX_2DriveAxis(self,dch,md,mx=None,my=None,tx=None,ty=None,cx=None,cy=None):
        global gb_Is_busyflg_A
        global gb_Is_busyflg_B
        global gb_Is_busyflg_C
        global gb_Is_busyflg_D
        global gb_devicename
        global gb_Interval_Time
        global gb_2Dext

        _devname = gb_devicename
        _dublech = dch
        _mode = md
        _motorX = mx
        _motorY = my
        _valX = tx
        _valY = ty
        _cirX = cx
        _cirY = cy
        _sdch = ''
        _sdchn = '0'
        _para5 = '0'
        _rt = 'Er:'
        rt = 'Ok:'

        if((_mode == 'ALN') or(_mode == 'RLN')):
            _para5 = '1'

        if((_motorX is None) or (_motorY is None) or (_valX is None) or (_valY is None)):
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_para5 == '0') and ((_cirX is None) or (_cirY is None))):
            rt = _rt + ' Bad parameter.'
            return(rt)

        try:
            _motorXi = int(_motorX)
            _motorYi = int(_motorY)
        except ValueError:
            rt = _rt + ' Bad motor number.'
            return(rt)
        if(((_motorXi < 0) or(_motorXi >15)) or ((_motorYi < 0) or(_motorYi >15)) or (_motorXi == _motorYi)):
            rt = _rt + ' Bad Motor Number.'
            return(rt)
        else:
            _mnxX = format(_motorXi,'X')
            _mnxY = format(_motorYi,'X')
        try:
            _valXi = int(_valX)
            _valYi = int(_valY)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        if(_para5 == '0'):
            try:
                _cirXi = int(_cirX)
                _cirYi = int(_cirY)
            except ValueError:
                rt = _rt + ' Bad parameter.'
                return(rt)
        
        if((_valXi < -999999999) or (_valXi > 999999999) or (_valYi < -999999999) or (_valYi > 999999999)):
            rt = _rt + ' Data out of range.'
            return(rt)
        else:
            if(_valXi >= 0):
                _valX = '+' + _valX
            if(_valYi >= 0):
                _valY = '+' + _valY
        if(_para5 == '0'):
            if ((_cirXi < -999999999) or (_cirXi > 999999999) or (_cirYi < -999999999) or (_cirYi > 999999999)):
                rt = _rt + ' Data out of range.'
                return(rt)
            else:
                if(_cirXi >= 0):
                    _cirX = '+' + _cirX
                if(_cirYi >= 0):
                    _cirY = '+' + _cirY

####
        if(_dublech is None ):
            _bsyA = self.Ctl_IsBusy('A')
            _bsyB = self.Ctl_IsBusy('B')
            if( (_bsyA == '1') or (_bsyB == '1')):
                _sdch = '1'
            else:
                _sdch = '0'
                _sdchn = '1'
#        elif((_dublech == 'AB') or (_dublech == '0')):
        elif(_dublech == 'AB'):
            _sdch = '0'
        elif(_dublech == 'CD'):
            _sdch = '1'
        else:
            rt = _rt + ' Incorrect channel selection.'
            return(rt)

        _rol = self.Ctl_GetFunction()
        if(_rol == '0'):
            rt = _rt + ' Offline.'
            return(rt)
        _mbsyX = self.Motor_IsBusy(_mnxX)
        if(_mbsyX == '1'):
            rt = _rt + ' Motor for X-axis is busy.'
            return(rt)
        _mbsyY = self.Motor_IsBusy(_mnxY)
        if(_mbsyY == '1'):
            rt = _rt + ' Motor for Y-axis is busy.'
            return(rt)

        if((_sdch == '0') and (_sdchn == '0')):
            _bsyA = self.Ctl_IsBusy('A')
            _bsyB = self.Ctl_IsBusy('B')
            if( (_bsyA == '1') or (_bsyB == '1')):
                rt = _rt + ' Busy.'
                return(rt)
            else:
                _sdchn = '1'        
        if((_sdch == '0') and (_sdchn == '1')):
            _fcx = self.CtlX_SelectForce('A',_mnxX)
            _fcy = self.CtlX_SelectForce('B',_mnxY)
            if(('Er:' in _fcx) or ('Er:' in _fcy)):
                rt = _rt + ' Could not select.'
                return(rt)
            gb_Is_busyflg_A = _mnxX
            gb_Is_busyflg_B = _mnxY
        elif(_sdch == '1'):
            _bsyC = self.Ctl_IsBusy('C')
            _bsyD = self.Ctl_IsBusy('D')
            if( (_bsyC == '1') or (_bsyD == '1')):
                rt = _rt + ' Busy.'
                return(rt)
            else:
                _fcx = self.CtlX_SelectForce('C',_mnxX)
                _fcy = self.CtlX_SelectForce('D',_mnxY)
                if(('Er:' in _fcx) or ('Er:' in _fcy)):
                    rt = _rt + ' Could not select.'
                    return(rt)
                gb_Is_busyflg_C = _mnxX
                gb_Is_busyflg_D = _mnxY
        else:
            rt = _rt + ' Internal Error A.'
            return(rt)
        _mnameX = self.num2name(_mnxX)
        _mnameY = self.num2name(_mnxY)
        if(('Er:' in _mnameX) or ('Er:' in _mnameY)):
            rt = _rt + ' internal error B.'
            return(rt)
        _destsendstr =  str(_devname) + '.' + str(_mnameX) + '>System _ChangedIsBusy 1'
        st.send(_destsendstr)
        _destsendstr =  str(_devname) + '.' + str(_mnameY) + '>System _ChangedIsBusy 1'
        st.send(_destsendstr)
        gb_Interval_Time = INTERVAL_RUN
        if((gb_Is_busyflg_A != 'nE') and (gb_Is_busyflg_B != 'nE') and (gb_Is_busyflg_C != 'nE') and (gb_Is_busyflg_D != 'nE')):
            _destsendstr =  'System _ChangedCtlIsBusy 1'
            st.send(_destsendstr)

        _cmd = 'C' + _sdch + _mode + _mnxX + _mnxY + _valX + '/' + _valY
        if(_para5 == '0'):
            _cmd = _cmd + '/' + _cirX + '/' + _cirY
        self.device_send(_cmd)

        time.sleep(1)
        _csts = self.device_act('STS?')
        _rstsL = _csts.split('/')
        _sts = tuple(_rstsL[3])
        _stsA = int(_sts[0],16)
        _stsB = int(_sts[2],16)
        _stsC = int(_sts[4],16)
        _stsD = int(_sts[6],16)

        _stba = str(_stsA & 1)
        _stbc = str(_stsC & 1)
        _stblsa = str(_stsA & 2)
        _stblsb = str(_stsB & 2)
        _stblsc = str(_stsC & 2)
        _stblsd = str(_stsD & 2)
        if(_sdch == '0'):
            if(_stba == '1'):
                rt = _rt + ' Could not draw. Bad point data.'
                return(rt)
            elif((_stblsa == '2') or (_stblsb == '2')):
                rt = _rt + ' Could not draw. Stop by limit switch.'
                return(rt)
        else:
            if(_stbc == '1'):
                rt = _rt + ' Could not draw. Bad point data.'
                return(rt)
            elif((_stblsc == '2') or (_stblsd == '2')):
                rt = _rt + ' Could not draw. Stop by limit switch.'
                return(rt)
        gb_2Dext = '1'
        return(rt)
    
    def CtlX_SelectForce(self,ch,mnx):
        _cksts4 = 'R\w\w\w\w'
        _ch = ch
        _mnox =mnx
        _cmd = ''
        _cmd0 =''
        _rol = ''
        _rt = 'Er:'
        rt = 'Ok:'

        if(_ch == 'A'):
            _cmd0 = 'S11'
        elif(_ch == 'B'):
            _cmd0 = 'S12'
        elif(_ch == 'C'):
            _cmd0 = 'S15'
        elif(_ch == 'D'):
            _cmd0 = 'S16'
        else:
            rt = _rt + ' Bad Channel.'
            return(rt)
        _rol = self.rolbusy(_ch)
        if('Er:' in _rol):
            rt = _rol
            return(rt)
        _mbsy = self.Motor_IsBusy(_mnox)
        if('Er:' in _mbsy):
            rt = _mbsy
            return(rt)
        _cmd = 'S10'
        _dsts = self.device_act(_cmd)
        _ckr = re.match(_cksts4,_dsts)
        if(_ckr is None):
            rt = _rt + ' Could not get setting motor number.'
            return(rt)
        _dstschi = _dsts.lstrip('R')
        _tplsts = tuple(_dstschi)
        if(_ch == 'A'):
            _sts = _tplsts[0]
        elif(_ch == 'B'):
            _sts = _tplsts[1]
        elif(_ch == 'C'):
            _sts = _tplsts[2]
        elif(_ch == 'D'):
            _sts = _tplsts[3]
        else:
            rt = _rt + ' Internal Error.'
            return(rt)
        if(_sts == _mnox):
            return(rt)
        _cmd = _cmd0 + _mnox
        self.device_send(_cmd)
        _cmd = 'S10'
        for v in range(5):
            _dsts = self.device_act(_cmd)
            _ckr = re.match(_cksts4,_dsts)
            if(_ckr is None):
                rt = _rt + ' Could not get setting motor number.'
                return(rt)
            _dstschi = _dsts.lstrip('R')
            _tplsts = tuple(_dstschi)
            if((_ch == 'A') and (_mnox == _tplsts[0])):
                _ckmts = 'Ok:'
                break
            elif((_ch == 'B') and (_mnox == _tplsts[1])):
                _ckmts = 'Ok:'
                break
            elif((_ch == 'C') and (_mnox == _tplsts[2])):
                _ckmts = 'Ok:'
                break
            elif((_ch == 'D') and (_mnox == _tplsts[3])):
                _ckmts = 'Ok:'
                break
            else:
                _ckmts = v
                time.sleep(WAIT_SELECT)
        if('Ok:' in _ckmts):
                return(rt)
        rt = _rt + ' could not select.'
        return(rt)

    def Ctl_GetPause(self):
        _rt = 'Er:'
        rt = ''
        _cmd = 'PAUSE?'
        _rsts = self.device_act(_cmd)
        if((_rsts != 'ON') and (_rsts != 'OFF')):
            rt = _rt + ' Invalid status.'
        else:
            rt = _rsts
        return(rt)

    def Ctl_SetFunction(self,sd):
        _setd = sd
        _cmd = ''
        rt = 'Ok'
        if ( _setd == '0' ):
            _cmd = 'S1L'
        elif( _setd == '1'):
            _cmd = 'S1R'
        else:
            rt = 'Er: Bad parameter. Please set to 0:Local or 1:Remote.'
        if( _cmd != ''):
            dc.device_send(_cmd)
            for v in range(10):
                time.sleep(WAIT_SELECT)
                _rsts = dc.Ctl_GetFunction()
                if(_rsts == _setd):
                    rt = 'Ok:'
                    break
                else:
                    tr = v + 1
                    rt = 'Er: ' + 'Could not change function.'
        return(rt)

###################################################################
#   common function
###################################################################
    def num2name(self,mn):
        global gb_MotorNameList
        _mnlist = gb_MotorNameList
        _mname = None
        _mnoi = int(mn,16)
        for v in range(16):
            if( v == _mnoi):
                _mname = _mnlist[v]
                break
        if(_mname is None):
            rt = 'Er: Incorrect motor number.'
        else:
            rt = _mname
        return(rt)

    def rolbusy(self,ch=''):
        _ch = ch
        rt = 'Ok:'
        _rol = self.Ctl_GetFunction()
        if(_rol == '0'):
            rt = 'Er: Offline.'
            return(rt)
        _busy = self.Ctl_IsBusy(_ch)
        if(_busy == '1'):
            rt = 'Er: Busy.'
        return(rt)

    def chkint(self,val):
        _data = val
        try:
            rt = int(_data)
        except ValueError:
            rt = 'Er: not int.'
        return(rt)

    def rolMbusy(self,mnx):
        _mnx = mnx

        rt = 'Ok:'
        _rol = self.Ctl_GetFunction()
        if(_rol == '0'):
            rt = 'Er: Offline.'
            return(rt)
        _busy = self.Motor_IsBusy(_mnx)
        if(_busy == '1'):
            rt = 'Er: Busy.'
        return(rt)

    def interval(self):
        global gb_Elaps
        global gb_Interval_Time
        global gb_Buf_Interval
        global gb_Is_busyflg_A
        global gb_Is_busyflg_B
        global gb_Is_busyflg_C
        global gb_Is_busyflg_D
        global INTERVAL_STOP
        global INTERVAL_RUN
        global REFRESH_RUN
        global gb_devicename
        global gb_2Dext

        if('.' in gb_devicename):
            _devname = gb_devicename.split('.')[0]
        else:
            _devname = gb_devicename
        gb_Elaps = time.time()
        if(gb_Interval_Time == INTERVAL_STOP):
            _printsts = self.Ctl_GetFunction()
            gb_Buf_Interval = REFRESH_RUN/INTERVAL_RUN
            return
        gb_Buf_Interval -= 1
        if(gb_Buf_Interval <= 0):
            if(gb_Is_busyflg_A != 'nE'):
                _stsA = self.Ctl_GetValue('A')
                _destsendstr =  str(_devname) + '.' + str(self.num2name(gb_Is_busyflg_A))  + '>System _ChangedValue ' + _stsA
                st.send(_destsendstr)
            if(gb_Is_busyflg_B != 'nE'):
                _stsB = self.Ctl_GetValue('B')
                _destsendstr =  str(_devname)  + '.' + str(self.num2name(gb_Is_busyflg_B)) + '>System _ChangedValue ' + _stsB
                st.send(_destsendstr)
            if(gb_Is_busyflg_C != 'nE'):
                _stsC = self.Ctl_GetValue('C')
                _destsendstr =  str(_devname)  + '.' + str(self.num2name(gb_Is_busyflg_C)) + '>System _ChangedValue ' + _stsC
                st.send(_destsendstr)
            if(gb_Is_busyflg_D != 'nE'):
                _stsD = self.Ctl_GetValue('D')
                _destsendstr =  str(_devname)  + '.' + str(self.num2name(gb_Is_busyflg_D)) + '>System _ChangedValue ' + _stsD
                st.send(_destsendstr)
            gb_Buf_Interval = REFRESH_RUN/INTERVAL_RUN
        if(gb_Is_busyflg_A != 'nE'):
            if ( not ((self.pm16c_getstatus('A')) & 0x1)):
                if((gb_Is_busyflg_B != 'nE') and (gb_Is_busyflg_C != 'nE') and (gb_Is_busyflg_D != 'nE')):
                    _destsendstr =  'System _ChangedCtlIsBusy 0'
                    st.send(_destsendstr)
                elif((gb_Is_busyflg_B == 'nE') and (gb_Is_busyflg_C == 'nE') and (gb_Is_busyflg_D == 'nE')):
                    gb_Interval_Time = INTERVAL_STOP
                _stsA = self.Ctl_GetValue('A')
                _destsendstr =  str(_devname) + '.' + str(self.num2name(gb_Is_busyflg_A)) + '>System _ChangedValue ' + _stsA
                st.send(_destsendstr)
                if(gb_2Dext == '1'):
                    gb_2Dext = '0'
                else:
                    _destsendstr =  str(_devname) + '.' + str(self.num2name(gb_Is_busyflg_A)) + '>System _ChangedIsBusy 0 '
                    st.send(_destsendstr)
                    gb_Is_busyflg_A = 'nE'
        if(gb_Is_busyflg_B != 'nE'):
            if ( not (self.pm16c_getstatus('B')) & 0x1):
                if((gb_Is_busyflg_A != 'nE') and (gb_Is_busyflg_C != 'nE') and (gb_Is_busyflg_D != 'nE')):
                    _destsendstr =  'System _ChangedCtlIsBusy 0'
                    st.send(_destsendstr)
                elif((gb_Is_busyflg_A == 'nE') and (gb_Is_busyflg_C == 'nE') and (gb_Is_busyflg_D == 'nE')):
                    gb_Interval_Time = INTERVAL_STOP
                _stsB = self.Ctl_GetValue('B')
                _destsendstr =  str(_devname) + '.' + str(self.num2name(gb_Is_busyflg_B)) + '>System _ChangedValue ' + _stsB
                st.send(_destsendstr)
                if(gb_2Dext == '1'):
                    gb_2Dext = '0'
                else:
                    _destsendstr =  str(_devname) + '.' + str(self.num2name(gb_Is_busyflg_B)) + '>System _ChangedIsBusy 0 '
                    st.send(_destsendstr)
                    gb_Is_busyflg_B = 'nE'
        if(gb_Is_busyflg_C != 'nE'):
            if ( not (self.pm16c_getstatus('C')) & 0x1):
                if((gb_Is_busyflg_A != 'nE') and (gb_Is_busyflg_B != 'nE') and (gb_Is_busyflg_D != 'nE')):
                    _destsendstr =  'System _ChangedCtlIsBusy 0'
                    st.send(_destsendstr)
                elif((gb_Is_busyflg_A == 'nE') and (gb_Is_busyflg_B == 'nE') and (gb_Is_busyflg_D == 'nE')):
                    gb_Interval_Time = INTERVAL_STOP
                _stsC = self.Ctl_GetValue('C')
                _destsendstr =  str(_devname) + '.' + str(self.num2name(gb_Is_busyflg_C)) + '>System _ChangedValue ' + _stsC
                st.send(_destsendstr)
                if(gb_2Dext == '1'):
                    gb_2Dext = '0'
                else:
                    _destsendstr =  str(_devname) + '.' + str(self.num2name(gb_Is_busyflg_C)) + '>System _ChangedIsBusy 0 '
                    st.send(_destsendstr)
                    gb_Is_busyflg_C = 'nE'
        if(gb_Is_busyflg_D != 'nE'):
            if ( not (self.pm16c_getstatus('D')) & 0x1):
                if((gb_Is_busyflg_A != 'nE') and (gb_Is_busyflg_B != 'nE') and (gb_Is_busyflg_C != 'nE')):
                    _destsendstr =  'System _ChangedCtlIsBusy 0'
                    st.send(_destsendstr)
                elif((gb_Is_busyflg_A == 'nE') and (gb_Is_busyflg_B == 'nE') and (gb_Is_busyflg_C == 'nE')):
                    gb_Interval_Time = INTERVAL_STOP
                _stsD = self.Ctl_GetValue('D')
                _destsendstr =  str(_devname) + '.' + str(self.num2name(gb_Is_busyflg_D)) + '>System _ChangedValue ' + _stsD
                st.send(_destsendstr)
                if(gb_2Dext == '1'):
                    gb_2Dext = '0'
                else:
                    _destsendstr =  str(_devname) + '.' + str(self.num2name(gb_Is_busyflg_D)) + '>System _ChangedIsBusy 0 '
                    st.send(_destsendstr)
                    gb_Is_busyflg_D = 'nE'
        return

    def intervalX(self):
        global gb_Elaps
        global gb_Interval_Time
        global gb_Buf_Interval
        global gb_Is_busyflg_A
        global gb_Is_busyflg_B
        global gb_Is_busyflg_C
        global gb_Is_busyflg_D
        global INTERVAL_STOP
        global INTERVAL_RUN
        global REFRESH_RUN
        global gb_devicename
        global gb_2Dext

        if('.' in gb_devicename):
            _devname = gb_devicename.split('.')[0]
        else:
            _devname = gb_devicename

        _rstsL = []
        _rol = ''
        rt = ''

        gb_Elaps = time.time()
        if(gb_Interval_Time == INTERVAL_STOP):
            self.Ctl_GetFunction()
            gb_Buf_Interval = REFRESH_RUN/INTERVAL_RUN
            return

        gb_Buf_Interval -= 1

        _rsts = self.device_act('STS?')
        _rstsL = _rsts.split('/')
        if(len(_rstsL) != 8):
            _now = self.pm16c_getnow()
            rt = _now + 'Ng: Bad Internal ' + str(_rsts)
            return(rt)
        if('R' in _rstsL[0]):
            _rol = '1'
            _chmno = _rstsL[0].lstrip('R')
        elif('L' in _rstsL[0]):
            _rol = '0'
            _chmno = _rstsL[0].lstrip('L')
        else:
            _now = self.pm16c_getnow()
            rt = _now + 'Ng: Bad Internal ' + str(_rsts)
            return(rt)
        _flgbusy = [gb_Is_busyflg_A,gb_Is_busyflg_B,gb_Is_busyflg_C,gb_Is_busyflg_D]
        _mns = tuple(_chmno)
        _sts = tuple(_rstsL[3])
        _xxs = [_rstsL[4],_rstsL[5],_rstsL[6],_rstsL[7]]

        _stba = (int(_sts[0],16) & 1)
        _stbb = (int(_sts[2],16) & 1)
        _stbc = (int(_sts[4],16) & 1)
        _stbd = (int(_sts[6],16) & 1)
        _stb = [_stba,_stbb,_stbc,_stbd]


        if(gb_Buf_Interval <= 0):
            for v in range(4):
                if(_flgbusy[v] == _mns[v]):
                    _loct = _xxs[v].lstrip('+')
                    _xxs[v] = _loct.lstrip('0')
                    if(_xxs[v] == ''):
                        _xxs[v] = '0'
                    _destsendstr =  str(_devname) + '.' + str(self.num2name(_mns[v])) + '>System _ChangedValue ' + _xxs[v]
                    st.send(_destsendstr)
                elif(_flgbusy[v] != 'nE'):
                    _now = self.pm16c_getnow()
                    rt = str(_now) + 'Ng: Bad Internal. Incorrect motor and channel settings.'
                    print(rt)
            gb_Buf_Interval = REFRESH_RUN/INTERVAL_RUN
#
        if( gb_2Dext == '1'):
            gb_2Dext = '0'
            return
#
        for v in range(4):
            if(_flgbusy[v] == _mns[v]):
                vs = 1 + 2*v
                if((int(_sts[vs],16) & 1) == 0):
                    if((_flgbusy[0] == _mns[0]) and (_flgbusy[1] == _mns[1]) and (_flgbusy[2] == _mns[2]) and (_flgbusy[3] == _mns[3])):
                        _destsendstr = 'System _ChangedCtlIsBusy 0'
                        st.send(_destsendstr)
                    _loct = _xxs[v].lstrip('+')
                    _xxs[v] = _loct.lstrip('0')
                    if(_xxs[v] == ''):
                        _xxs[v] = '0'
                    _destsendstr =  str(_devname) + '.' + str(self.num2name(_mns[v])) + '>System _ChangedValue ' + _xxs[v]
                    st.send(_destsendstr)
                    _destsendstr =  str(_devname) + '.' + str(self.num2name(_mns[v])) + '>System _ChangedIsBusy 0'
                    st.send(_destsendstr)
                    _flgbusy[v] = 'nE'
                    if((_flgbusy[0] == 'nE') and (_flgbusy[1] == 'nE') and (_flgbusy[2] == 'nE') and (_flgbusy[3] == 'nE')):
                        gb_Interval_Time = INTERVAL_STOP
            elif(_flgbusy[v] != 'nE'):
                _now = self.pm16c_getnow()
                rt = str(_now) + 'Ng: Bad Internal. Incorrect motor and channel settings.'
                print(rt)
        gb_Is_busyflg_A = _flgbusy[0]
        gb_Is_busyflg_B = _flgbusy[1]
        gb_Is_busyflg_C = _flgbusy[2]
        gb_Is_busyflg_D = _flgbusy[3]
        return


###################################################################
#   Motor command execution procedure
###################################################################
    def Motor_IsBusy(self,mnox):
        global gb_Is_busyflg_A
        global gb_Is_busyflg_B
        global gb_Is_busyflg_C
        global gb_Is_busyflg_D
        _FlgBusy_A = gb_Is_busyflg_A
        _FlgBusy_B = gb_Is_busyflg_B
        _FlgBusy_C = gb_Is_busyflg_C
        _FlgBusy_D = gb_Is_busyflg_D
        _mnx = mnox
        _rt = '0'
        if((_FlgBusy_A != 'nE') and (_FlgBusy_A == _mnx) ):
            _rt = '1'
        elif((_FlgBusy_B != 'nE') and (_FlgBusy_B == _mnx) ):
            _rt = '1'
        elif((_FlgBusy_C != 'nE') and (_FlgBusy_C == _mnx) ):
            _rt = '1'
        elif((_FlgBusy_D != 'nE') and (_FlgBusy_D == _mnx) ):
            _rt = '1'
        return(_rt)

    def Motor_GetSelected(self,mn):
        global gb_MotorNameList
        _cksts = 'R\w\w\w\w'
        _motlist = []
        _motname = mn
        _motlist = gb_MotorNameList
        _mno = ''
        _mnox = ''
        _rt = 'Er:'
        rt = 'Ok:'

        for v in range(0,16):
            if(_motname == _motlist[v]):
                _mno = int(v)
#                _rt = 'InList'
                break
            else:
                rt = _rt + ' Motorname not in list'
        if( 'Er:' in rt):
            return(rt)
        _mnox = format(_mno,'X')
        _cmd = 'S10'
        _dsts = self.device_act(_cmd)
        _ckr = re.match(_cksts,_dsts)
        if(_ckr is None):
            rt = _rt + ' Could not get setting motor number.'
            return(rt)
        _dstschi = _dsts.lstrip('R')
        _tplsts = tuple(_dstschi)
        if(str(_mnox) == _tplsts[0]):
            rt = 'A'
        elif(str(_mnox) == _tplsts[1]):
            rt = 'B'
        elif(str(_mnox) == _tplsts[2]):
            rt = 'C'
        elif(str(_mnox) == _tplsts[3]):
            rt = 'D'
        else:
            rt = 'N'
        return(rt)

#    def Motor_GetCancelBacklash(self,mn,*ml):
    def Motor_GetCancelBacklash(self,mn):
        global gb_CancelBacklash
        _mno = mn
        _mnoi = int(_mno)
        _mnox = format(_mnoi,'X')
        _rt = 'Er:'
        _cmd = 'B' + str(_mnox) + '?'
        _rdt = self.device_act(_cmd)
        if('0000' in _rdt):
            _rt = '0'
        elif('+' in _rdt):
            _rt0 = _rdt.lstrip('+')
            _rt1 = _rt0.lstrip('0')
            _rt =  _rt1
        elif('-' in _rdt):
            _rt0 = _rdt.lstrip('-')
            _rt1 = _rt0.lstrip('0')
            _rt = '-' + _rt1
        else:
            _rt = _rt + ' Invalid reply value.'
        if('Er:' not in _rt):
            gb_CancelBacklash[_mnoi] = _rt
        return(_rt)

    def Motor_SetCancelBacklash(self,mn,sd):
        global gb_CancelBacklash
        _mno = mn
        _sd = sd
        _mnoi = int(_mno)
        _mnox = format(_mnoi,'X')
        _com0 = 'B' + _mnox
        _rt = 'Er:'
        try:
            _sdi = int(_sd)
        except ValueError:
            rt = _rt + ' Bad data Number.'
            return(rt)

        _rol = self.Ctl_GetFunction()
        if(_rol == '0'):
            rt = _rt + ' Offline.'
            return(rt)
        _busy = self.Motor_IsBusy(_mnox)
        if(_busy == '1'):
            rt = _rt + ' Busy.'
            return(rt)
        if(_sdi >= 0):
            _sdf = '{:04d}'.format(_sdi)
            _sdc = '+' + str(_sdf)
        else:
            _sdf = '{:05d}'.format(_sdi)
            _sdc = str(_sdf)
        _com = _com0 + _sdc
        self.device_send(_com)
        time.sleep(0.04)
        gb_CancelBacklash[_mnoi] = _sdc
        return('Ok:')

    def Motor_GetValue(self,mn):
        _mn = mn
        _stn = '0'
        _rt = self.pm16c_getm3bytes(_mn,_stn)
        return(_rt)

    def MotorX_GetAccRateCode(self,mnx):
        _mnox = mnx
        # need to convert to hexa  20221006
        _cmd = 'RTE?' + str(_mnox)
        _rdt = self.device_act(_cmd)
        _rt = _rdt.lstrip('0')
        return(_rt)

    def Motor_GetAccRateCode(self,mnx):
        _mnox = mnx
        _cmd1 = 'C'
        _rdt = self.pm16c_getm1byte(_mnox,_cmd1)
        _rt = _rdt.lstrip('0')
        return(_rt)


    def MotorX_GetAccRate(self,mnx):
        _mnox = mnx
        _cmd = 'RTE?' + str(_mnox)
        _rt = ''
        _rdt = self.device_act(_cmd)
        _rt = self._AccelarationRate[int(_rdt)]
        return(_rt)

    def Motor_GetAccRate(self,mnx):
        _mnox = mnx
        _cmd1 = 'C'
        _rt = ''
        _rdt = self.pm16c_getm1byte(_mnox,_cmd1)
        _rt = self._MotorSpeedRate[int(_rdt)]
        return(_rt)

    def Motor_GetAutoChangeSpeed(self,mnx,ln):
        _mnox = mnx
        _lno = ln
        _cmd =''
        _rd =[]
        _rt = 'Er:'
        rt = ''
        try:
            _lnoi = int(_lno)
        except ValueError:
            rt = _rt + ' Bad data Number.'
            return(rt)
        if( _lnoi < 0 or _lnoi >127):
            rt = _rt + ' Bad data Number.'
        _lnop = "{:0>3}".format(_lnoi)
        _cmd = 'ACS?' + str(_mnox) + str(_lnop)
        _rdt = self.device_act(_cmd)
        _rd = _rdt.split('/')
        del _rd[0]
        if(len(_rd) == 4):
            _rd[3] = _rd[3].lstrip('0')
        if(len(_rd)>=3):
            _rd[1] = _rd[1].lstrip('0')
        rt = (" ".join(_rd))
        return(rt)

    def Motor_SetAutoChangeSpeed(self,mnx,*para):
        _parameters = []
        _mnox = mnx
        _parameters = para
        _cmd = 'ACS' + str(_mnox)
        _rt = 'Er:'
        _rt = ''

        if(len(_parameters)==2):
            if(_parameters[1]!='END'):
                rt = _rt + ' Bad parameters.'
                return(rt)
        elif(len(_parameters)==3):
            rt = _rt + ' Bad parameters.'
            return(rt)
        elif(len(_parameters)==4):
            if((_parameters[3]!='SLW') and (_parameters[3]!='FST') and (_parameters[3]!='NOP')):
                rt = _rt + ' Bad parameters.'
                return(rt)
        else:
            if((_parameters[3]!='SPD') and (_parameters[3]!='RTE')):
                rt = _rt + ' Bad parameters.'
                return(rt)

        try:
            _rncki = int(_parameters[0])
        except ValueError:
            rt = _rt + ' Bad register number.'
            return(rt)
        if( (_rncki < 0) or (_rncki > 127)):
            rt = _rt + ' Bad register number.'
            return(rt)
        _regn = "{:0>3}".format(_rncki)
        if( _parameters[1] == 'END'):
            _cmd = _cmd + _regn + '/' + _parameters[1]
        else:
            try:
                _dti = int(_parameters[2])
            except ValueError:
                rt = _rt + ' Bad parameter.'
                return(rt)
            if((_dti < -2147483647) or (_dti > 2147483647) ):
                rt = _rt + ' Data out og range.'
                return(rt)
            if((_parameters[1] == 'ADD') or (_parameters[1] == 'TIM') or (_parameters[1] == 'ACC') or (_parameters[1] == 'DCC')):
                if((_parameters[3] == 'SLW') or (_parameters[3] == 'FST') or (_parameters[3] == 'NOP')):
                    _cmd = _cmd + _regn + '/' + _parameters[1] + '/' + _parameters[2] + '/' + _parameters[3]
                else:
                    try:
                        _dti = int(_parameters[4])
                    except ValueError:
                        rt = _rt + ' Bad parameter.'
                        return(rt)
                    if((_dti < 1) or (_dti > 5000000) ):
                        rt = _rt + ' Data out og range.'
                        return(rt)
                    _cmd = _cmd + _regn + '/' + _parameters[1] + '/' + _parameters[2] + '/' + _parameters[3] + '/' + _parameters[4]
        self.device_send(_cmd)
        rt = 'Ok:'
        return(rt)

    def Motor_GetAutoChangeSpeedReady(self,mnx):
        _mnox = mnx
        _cmd = 'ACSP?' + str(_mnox)
        _rt = 'Er:'
        _rdt = self.device_act(_cmd)
        if( 'ready' in _rdt ):
            if('not' in _rdt):
                _rt = '0'
            else:
                _rt = '1'
        else:
            _rt = _rt + ' Data value error.'
        rt = _rt
        return(rt)

    def MotorX_SetAutoChangeSpeedReady(self,mn,sd):
        global gb_MotorBusy
        _MotorBusy = gb_MotorBusy
        _mno = mn
        _setdata = sd
        _rt = 'Er:'
        rt ='Ok:'
        _cmd =''

        _mnoi = int(_mno)
        _mnox = format(_mnoi,'X')
        
        _rolb = self.rolMbusy(_mnox)
        if('Er:' in _rolb):
            rt = _rolb
            return(rt)
        if(_setdata == '0' ):
            _cmd = 'ACSC' + str(_mnox)
        elif(_setdata == '1'):
            _cmd = 'ACSP' + str(_mnox)
        else:
            rt = _rt + ' Bad parameter.'
        if( 'Ok:' in rt):
            self.device_send(_cmd)
        return(rt)

    def Motor_GetDigitalCwLs(self,mn):
        _mno = mn
        _scmd = '3'
        _rdt = self.pm16c_getm3bytes(_mno,_scmd)
        return(_rdt)
        
    def Motor_SetDigitalCwLs(self,mn,sd):
        _mnox = mn
        _dti = sd
        _scmd = '3'
        _rdt = self.pm16c_setm3bytes(_mnox,_dti,_scmd)
        return(_rdt)

    def Motor_GetDigitalCcwLs(self,mn):
        _mno = mn
        _scmd = '6'
        _rdt = self.pm16c_getm3bytes(_mno,_scmd)
        return(_rdt)
    
    def Motor_SetDigitalCcwLs(self,mn,sd):
        _mnox = mn
        _dti = sd
        _scmd = '6'
        _rdt = self.pm16c_setm3bytes(_mnox,_dti,_scmd)
        return(_rdt)

    def Motor_GetHMLspeed(self,mnx,sp):
        global gb_pm16cx
        pm16cx = gb_pm16cx
        _mnox = mnx
        _spf = sp
        if(pm16cx == 'on'):
            _rdt = self.pm16cX_getspeedcommon(_mnox,_spf)
        else:
            if(_spf == 'H'):
                _spf = '9'
            elif(_spf == 'M'):
                _spf = 'A'
            elif(_spf == 'L'):
                _spf = 'B'
            _rdt0 = self.pm16c_getm1byte(_mnox,_spf)
            _rdt0i = int(_rdt0,16)
            _rdt = self.pm16c_code2speed(_rdt0i)
        rt = str(_rdt)
        return(rt)

    def Motor_Stop(self,mn,md=''):
        _mne = mn
        _mode = md
        _rt = 'Er:'
        rt ='Ok:'
        _chsts = self.Motor_GetSelected(_mne)
        if('Er:' in _chsts):
            rt = _chsts
        elif(_chsts == 'N'):
            rt = _rt + ' Not set to channel.'
        else:
            self.Ctl_Stop(_chsts,_mode)
        return(rt)

    def Motor_SetHold(self,mnx,hld):
        _mnox = mnx
        _hld = hld
        _verl = []
        _cmd = 'VER?'
        _rt = 'Er:'
        rt = 'Ok:'

        _rvd = self.device_act(_cmd)
        if('Timeout' in _rvd):
            rt = _rt + ' Not supported in this ROM version.'
            return(rt)
        else:
            _verl = _rvd.split(' ')
            _Romversioni = float(_verl[0])
            if(_Romversioni < 1.17):
                rt = _rt + ' Not supported in this ROM version.'
                return(rt)

        _rolb = self.rolMbusy(_mnox)
        if('Er:' in _rolb):
            rt = _rolb
            return(rt)

        if((_hld == '1') or (_hld == 'ON') ):
            _cmd = 'HOLD' + _mnox + 'ON'
            self.device_send(_cmd)
            time.sleep(WAIT_HOLD_ON)
        elif((_hld == '0') or (_hld == 'OFF')):
            _cmd = 'HOLD' + _mnox + 'OFF'
            self.device_send(_cmd)
            time.sleep(WAIT_HOLD_OFF)
        else:
            rt = 'Er: Bad parameter.'
        return(rt)

    def Motor_GetHold(self,mnx):
        _mnox = mnx
        _verl = []
        _cmd = 'VER?'

        _rvd = self.device_act(_cmd)
        if('Timeout' in _rvd):
            rt = _rt + ' Not supported in this ROM version.'
            return(rt)
        else:
            _verl = _rvd.split(' ')
            _Romversioni = float(_verl[0])
            if(_Romversioni < 1.17):
                rt = _rt + ' Not supported in this ROM version.'
                return(rt)

        _cmd = 'HOLD?' + _mnox
        rt  = self.device_act(_cmd)
        return(rt)


    def Motor_GetLimits(self,mn):
        global gb_pm16cx
        pm16cx = gb_pm16cx
        _mno = mn
        _mnoi = int(_mno)
        _mnox = format(_mnoi,'X')
        if(pm16cx == 'on'):
            rt = self.MotorX_GetLimits(_mnox)
            return(rt)
        else:
            _rt = self.pm16c_getm1byte(_mnox,'D')
            _rti = int(_rt,16)
            rt = '{:b}'.format(_rti)
        return(rt)

    def MotorX_GetLimits(self,mnx):
        _mnox = mnx
        _cmd = 'SETLS?' + _mnox
        _rt = self.device_act(_cmd)
        return(_rt)

    def Motor_SetLimits(self,mnx,sd):
        global gb_pm16cx
        pm16cx = gb_pm16cx
        _mnox = mnx
        _sdata = sd
        _rt = 'Er:'
        rt = 'Ok:'

        _sts = self.rolMbusy(_mnox)
        if('Er:' in _sts):
            rt = _sts
            return(rt)

        if( pm16cx == 'on'):
            rt = self.MotorX_SetLimits(_mnox,_sdata)
            return(rt)

        _cmd = 'S5'
        try:
            _ckdbi = int(_sdata,2)
        except ValueError:
            rt = _rt + ' Data invalid.'
            return(rt)
        if(_ckdbi > 256):
            rt = _rt + ' Data invalid.'
            return(rt)
        else:
            _sdataxt = format(_ckdbi,'2X')
            _sdatax = _sdataxt.zfill(2)
        
        _cmd = _cmd + _mnox + 'D' + _sdatax
        self.device_send(_cmd)
        time.sleep(0.04)
        return(rt)

    def MotorX_SetLimits(self,mnx,sd):
        _mnox = mnx
        _sdata = sd
        _cmd = 'SETLS'
        _rt = 'Er:'
        rt = 'Ok:'

        try:
            _ckdbi = int(_sdata,2)
        except ValueError:
            rt = _rt + ' Data invalid.'
            return(rt)
        if(_ckdbi > 256):
            rt = _rt + ' Data invalid.'
            return(rt)
        else:
            _ckdbick = _ckdbi & 0x08
            if(_ckdbick != 0):
                rt = _rt + ' Data invalid.'
                return(rt)
#            _sdataxt = format(_ckdbi,'2X')
#            _sdatax = _sdataxt.zfill(2)
        _cmd = _cmd + _mnox + _sdata
        self.device_send(_cmd)
        time.sleep(0.04)
        return(rt)
            
        



    def MotorX_GetHPValue(self,mnx):
        _mnox = mnx
        _cmd =''
        rt = ''
#        _mnoi = int(_mno)
#        _mnox = format(_mnoi,'X')
        _cmd = 'SHP?' + _mnox
        _rst = self.device_act(_cmd)
        if('NO' in _rst):
            rt = 'Ng: No HomePosition.'
            return(rt)
        if('+' in _rst):
            _rst0 = _rst.lstrip('+')
            _rsti = int(_rst0)
            if(_rsti == 0):
                rt = '0'
            else:
                rt = _rst0.lstrip('0')
        else:
            _rst0 = _rst.lstrip('-')
            _rst1 = _rst0.lstrip('0')
            rt = '-' + _rst1
        return(rt)

    def MotorX_HPPreset(self,mnx,sd):
        _mnox = mnx
        _setdata = sd
        _cmd = ''
        _rt = 'Er:'
        rt = 'Ok:'

        _sdti = int(_setdata)
        if((_sdti < -2147483647) or (_sdti > 2147483647)):
            rt = _rt + ' Data out of range.'
            return(rt)
        _rol = self.Ctl_GetFunction()
        if(_rol == '0'):
            rt = _rt + ' Offline.'
            return(rt)
        _isbusy = self.Motor_IsBusy(_mnox)
        if(_isbusy == '1'):
            rt = _rt + ' Busy.'
            return(rt)
        if(_sdti >= 0):
            _sdt = '+' + str(_sdti)
        else:
            _sdt = str(_sdti)
        _cmd = 'SHP' + _mnox + _sdt
        self.device_send(_cmd)
        return(rt)

    def MotorX_GetHPsettings(self,mnx):
        _mnox = mnx
        _cmd = 'SETHP?' + _mnox
        rt = self.device_act(_cmd)
        return(rt)

    def MotorX_SetHPsettings(self,mnx,sd):
        _ckstd3 = '[0][0|1]{3}'
        _mnox =mnx
        _sdata = sd
        _rt = 'Er:'
        rt = 'Ok:'

        _cksts = re.match(_ckstd3,_sdata)
        if(_cksts == None):
            rt = _rt + ' Data invalid.'
            return(rt)        
        _rol = self.Ctl_GetFunction()
        if(_rol == '0'):
            rt = _rt + ' Offline.'
            return(rt)
        _isbusy = self.Motor_IsBusy(_mnox)
        if(_isbusy == '1'):
            rt = _rt + ' Busy.'
            return(rt)

        _cmd = 'SETHP' + _mnox + str(_sdata)
        self.device_send(_cmd)
        return(rt)

    def MotorX_GetHPOffset(self,mnx):
        _ckstd4 = '[\d]{4}'
        _mnox = mnx
        _rt = 'Er:'
        _cmd = 'SHPF?' + _mnox
        _rst = self.device_act(_cmd)
        _ckrst = str(_rst)
        _csts = re.match(_ckstd4,_ckrst)
        if(_csts == None):
            rt = _rt + ' read data invalid.'
        else:
            rt = _ckrst
        return(rt)

    def MotorX_SetHPOffset(self,mnx,sd):
        _mnox = mnx
        _sdata = sd
        _rt = 'Er:'
        rt = 'Ok:'

        try:
             _sdti = int(_sdata)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_sdti < 0) or (_sdti > 9999)):
            rt = _rt + ' Bad parameter.'
            return(rt)
        _rol = self.Ctl_GetFunction()
        if((_rol == '0')):
            rt = _rt + ' Offline.'
            return(rt)
        _isbusy = self.Motor_IsBusy(_mnox)
        if(_isbusy == '1'):
            rt = _rt + ' Busy.'
            return(rt)
        _cmd = 'SHPF' + _mnox + _sdata
        self.device_send(_cmd)
        return(rt)

    def MotorX_GetMotorSettings(self,mnx):
#        _mnoi = int(mn)
#        _mnox = format(_mnoi,'X')
        _mnox = mnx
        _cmd = 'SETMT?' + _mnox
        rt = self.device_act(_cmd)
        return(rt)

    def MotorX_SetMotorSettings(self,mnx,sd):
        _mnox = mnx
        _sdata= []
        _ver = ''
        _verf = 'good'
        _senddata = sd
        _sdata = tuple(sd)
        _cmd = ''
        _rt ='Er:'
        rt = 'Ok:'
        _rol = self.Ctl_GetFunction()
        if(_rol == '0'):
            rt = _rt + ' Offline.'
            return(rt)
        _isbusy = self.Motor_IsBusy(_mnox)
        if(_isbusy == '1'):
            rt = _rt + ' Busy.'
            return(rt)

        _ver = self.device_act('VERH?')
        _ver = _ver.split(' ')[1]
        try:
            _veri = int(_ver)
        except ValueError:
            _verf = 'bad'
        if((_verf == 'good') and (_veri <= 4)):
            _verf == 'bad'
        
        if((_sdata[0] != '0') and (_sdata[0] != '1')):
            rt = _rt + ' Data invalid.'
            return(rt)
        if((_sdata[1] != '0') and (_sdata[1] != '1')):
            rt = _rt + ' Data invalid.'
            return(rt)
        if((_sdata[2] != '0') and (_sdata[2] != '1') and (_sdata[2] != '2')):
            rt = _rt + ' Data invalid.'
            return(rt)
        if(_verf == 'good'):
            if((_sdata[3] != '0') and (_sdata[3] != '1') and (_sdata[3] != '2')):
                rt = _rt + ' Data invalid.'
                return(rt)
        else:
            if((_sdata[3] != '0') and (_sdata[3] != '1')):
                rt = _rt + ' Data invalid.'
                return(rt)
        
        _cmd = 'SETMT' + _mnox + _senddata
        self.device_send(_cmd)
        time.sleep(0.04)
        return(rt)

    def MotorX_SetSpeed(self,mnx,sd):
        _mnox = mnx
        _sdata = sd
        _rt = 'Er:'
        rt = 'Ok:'

        _rol = self.rolMbusy(_mnox)
        if('Er:' in _rol):
            rt = _rol
            return(rt)

        if((_sdata == 'H') or (_sdata == 'M') or (_sdata == 'L')):
            _cmd = 'SPD' + _sdata + _mnox
        else:
            try:
                _dck = int(_sdata)
            except ValueError:
                rt = _rt + ' Bad parameter.'
                return(rt)
            if( _dck < 1):
                _cmd = 'SPDL' + _mnox
            elif( _dck == 0):
                _cmd = 'SDDM' + _mnox
            else:
                _cmd = 'SPDH' + _mnox
        self.device_send(_cmd)
        time.sleep(WAIT_MEMWRITE)
        return(rt)

    def Motor_Preset(self,mnx,sd):
        global gb_devicename
        _devname = gb_devicename
        _mnox = mnx
        _sdata = sd

        _sts = self.rolMbusy(_mnox)
        if ('Er:' in _sts):
            return(_sts)
        
        try:
            _sdatai = int(_sdata)
        except ValueError:
            rt = 'Er: Bad parameter.'
            return(rt)

        if(_sdatai < 0):
            _datct = (_sdatai+1)*(-1)
            _sdatac = _datct ^ 0xffffff
        else:
            _sdatac = _sdatai

        _rsts = self.pm16c_setm3bytes(_mnox,_sdatac,'0')
        if(_rsts != ''):
            _destsendstr =  str(_devname)  + '.' + str(self.num2name(_mnox)) + '>System _ChangedIsBusy 1'
            st.send(_destsendstr)
        return(_rsts)

    def MotorX_ChangeSpeed(self,mnx,sd):
        _mnox = mnx
        _sdata = sd
        _cmd = 'SPC'
        _rt = 'Er:'
        rt = 'Ok:'

        try:
            _sdti = int(_sdata)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_sdti < 1) or (_sdti > 5000000)):
            rt = _rt + ' Data out of range.'
            return(rt)
        _sts = self.rolMbusy(_mnox)
        if('Er:' in _sts):
            rt = _sts
            return(rt)
        _cmd = _cmd + _mnox + _sdata
        self.device_send(_cmd)
        return(rt)

    def Motor_SetValue(self,mn,sd,md):
        _mno = mn
        _sdata = sd
        _mode = md
        _chsetting = []
        _rt = 'Er:'
        rt = 'Ok:'

        _mnoi = int(_mno)
        _mnox = format(_mnoi,'X')

        _sts = self.rolMbusy(_mnox)
        if('Er:' in _sts):
            rt = _sts
            return(rt)
        
        _chsetting = self.Ctl_GetSelected('INTERNAL')
        if(_chsetting[0] == _mnox):
            rt = self.pm16c_SetValue('A',_sdata,_mno,_mode)
        elif(_chsetting[1] == _mnox):
            rt = self.pm16c_SetValue('B',_sdata,_mno,_mode)
        elif(_chsetting[2] == _mnox):
            rt = self.pm16c_SetValue('C',_sdata,_mno,_mode)
        elif(_chsetting[3] == _mnox):
            rt = self.pm16c_SetValue('D',_sdata,_mno,_mode)
        else:
            _chbusy = self.Ctl_IsBusy('A')
            if(_chbusy == '0'):
                _cka = self.Ctl_Select('A',_mnox)
                if('Er:' in _cka):
                    rt = _rt + ' Execution does not proceed.'
                    return(rt)
                else:
                    rt = self.pm16c_SetValue('A',_sdata,_mno,_mode)
                    return(rt)
            _chbusy = self.Ctl_IsBusy('B')
            if(_chbusy == '0'):
                _cka = self.Ctl_Select('B',_mnox)
                if('Er:' in _cka):
                    rt = _rt + ' Execution does not proceed.'
                    return(rt)
                else:
                    rt = self.pm16c_SetValue('B',_sdata,_mno,_mode)
                    return(rt)
            _chbusy = self.Ctl_IsBusy('C')
            if(_chbusy == '0'):
                _cka = self.Ctl_Select('C',_mnox)
                if('Er:' in _cka):
                    rt = _rt + ' Execution does not proceed.'
                    return(rt)
                else:
                    rt = self.pm16c_SetValue('C',_sdata,_mno,_mode)
                    return(rt)
            _chbusy = self.Ctl_IsBusy('D')
            if(_chbusy == '0'):
                _cka = self.Ctl_Select('D',_mnox)
                if('Er:' in _cka):
                    rt = _rt + ' Execution does not proceed.'
                    return(rt)
                else:
                    rt = self.pm16c_SetValue('D',_sdata,_mno,_mode)
                    return(rt)
            rt = _rt + ' Busy'
        return(rt)

    def MotorX_SetMotorStop(self,mnx,sd):
        _mnox = mnx
        _sdata = sd
        _cmd = 'STOPMD'
        _rt = 'Er:'
        rt = 'Ok:'

        _sts = self.rolMbusy(_mnox)
        if('Er:' in _sts):
            rt = _sts
            return(rt)
        try:
            _ckd = int(_sdata,2)
        except ValueError:
            rt = _rt + ' Data invalid.'
            return(rt)
        if(_ckd > 3):
            rt = _rt + ' Data invalid.'
            return(rt)
        
        _sdt = _sdata.zfill(2)
        _cmd = _cmd + _mnox + _sdt
        self.device_send(_cmd)
        time.sleep(0.04)
        return(rt)

    def Motor_SetAccRate(self,mnx,sd):
        _mnox = mnx
        _spd = sd
        _cmd ='S5'
        _mad = 'C'
        rt = 'Ok:'

        _rsts = self.rolMbusy(_mnox)
        if('Er:' in _rsts):
            rt = _rsts
            return(rt)
        try:
            _spdi = int(_spd)
        except ValueError:
            rt = 'Er: Bad parameter.'
            return(rt)

        
        if(_spdi < 0):
            _spdi = 0
        _spdx = self.pm16c_rate2hexcode(_spdi)
        if('Er:' in _spdx):
            rt = _rated
            return(rt)
        _cmd = _cmd + _mnox + _mad + (_spdx)
        self.device_send(_cmd)
        time.sleep(WAIT_MEMWRITE)
        _rdt = self.pm16c_getm1byte(_mnox,_mad)
        _rated = self.pm16c_code2rate(_rdt)
        if(_spdi == _rated):
            rt = 'Ok'
        else:
            rt = 'Ok. In this case, set value = ' + str(_rated)
        return(rt)

    def MotorX_SetAccRate(self,mnx,sd):
        _mnox = mnx
        _sdata = sd
        _code = '0'
        _cmd = 'RTE'
        _rt = 'Er:'
        rt = 'Ok:'

        _sts = self.rolMbusy(_mnox)
        if('Er:' in _sts):
            rt = _sts
            return(rt)
        
        try:
            _ckdf = float(_sdata)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        
        _code = self.pm16cX_rate2code(_ckdf)
        _cmd = _cmd + _mnox + _code
        self.device_send(_cmd)
        return(rt)

    def MotorX_GetSpeedSelect(self,mnx):
        _mnox = mnx
        _cmd = 'SPD?' + _mnox
        _rt = 'Er:'
        rt = 'Ok:'
        _rd = self.device_act(_cmd)
        if( (_rd == 'HSPD') or (_rd == 'MSPD') or (_rd == 'LSPD')):
            _rdt = _rd.rstrip('SPD')
            rt = _rdt
        else:
            rt = _rt + ' Unable to read data.'
        return(rt)

    def MotorX_gettimingoutsetting(self,mnx,flg):
        _mnox =mnx
        _setflg = flg
        _rt = 'Er:'
        rt = ''
        if((_setflg != 'M') and (_setflg != 'S') and (_setflg != 'E') and (_setflg != 'I')):
            rt = _rt + ' Bad Internal ' + str(_setflg)
            return(rt)
        _cmd = 'TMG' + _setflg + '?' + _mnox
        _rsts = self.device_act(_cmd)
        if('+' in _rsts):
            _rsts = _rsts.lstrip('+')
        rt = _rsts.lstrip('0')
        if(rt == ''):
            rt = '0'
        return(rt)

    def MotorX_settimingoutsetting(self,mnx,flg,sd):
        _mnox =mnx
        _setflg = flg
        _setdata = sd
        _rt = 'Er:'
        rt ='Ok:'
        if(_setflg == 'M'):
            if((_setdata != '0') and (_setdata != '1') and (_setdata != '2') and (_setdata != '3') and (_setdata != '4') and (_setdata != '5')):
                rt = _rt + ' Data invalid.'
                return(rt)
        elif((_setflg == 'S') or (_setflg == 'E')):
            try:
                _setdatai = int(_setdata)
            except ValueError:
                rt = _rt + ' Data invalid.'
                return(rt)
            if((_setdatai < -2147483647) or (_setdatai > 2147483647)):
                rt = _rt + ' Data out of range.'
                return(rt)
        elif(_setflg == 'I'):
            try:
                _setdatai = int(_setdata)
            except ValueError:
                rt = _rt + ' Data invalid.'
                return(rt)
            if((_setdatai < 0) or (_setdatai > 2147483647)):
                rt = _rt + ' Data out of range.'
                return(rt)
        else:
            rt = _rt + ' Bad internal ' + str(_setflg)
            return(rt)
        _rsts = self.rolMbusy(_mnox)
        if('Er:' in _rsts):
            rt = _rsts
            return(rt)
        _rdt = self.MotorX_gettimingoutsetting(_mnox,_setflg)
        if(_rdt == ''):
            rt = _rt + ' Setting is null.'
            return(rt)
        elif(_setdata != _rdt):
            self.MotorX_SetTimingOutReady(_mnox,'0')
            time.sleep(WAIT_MEMWRITE)
        _cmd = 'TMG' + _setflg + _mnox + _setdata
        self.device_send(_cmd)
        return(rt)

    def MotorX_GetTimingOutReady(self,mnx):
        _mnox = mnx
        _cmd = 'TMGR?' + _mnox
        _rt = 'Er:'
        rt = ''
        _rsts = self.device_act(_cmd)
        if(_rsts == 'YES'):
            rt = '1'
        elif(_rsts == 'NO'):
            rt = '0'
        else:
            rt = _rt + ' Undefined read data.'
        return(rt)

    def MotorX_SetTimingOutReady(self,mnx,sf):
        _mnox = mnx
        _signf = sf
        _cmd = 'TMG'
        _scmd = ''
        _rt = 'Er:'
        rt = 'Ok:'
        if(_signf == '0'):
            _scmd = 'C'
        elif(_signf == '1'):
            _scmd = 'R'
        else:
            rt = _rt + ' Bad parameter.'
        _cmd = _cmd + _scmd + _mnox
        self.device_send(_cmd)
        return(rt)

    def MotorX_GetMotorStop(self,mnx):
        _mnox = mnx
        _cmd = 'STOPMD?' + _mnox
        _rsts = self.device_act(_cmd)
        return(_rsts)

    def Motor_Scan(self,mnx,md):
        _mnox = mnx
        _mode = md
        _mnxl = []
        _rt = 'Er:'
        rt = 'Ok:'

        _rst0 = self.rolbusy()
        if('Er:' in _rst0):
            rt = _rst0
            return(rt)
        _rst1 = self.rolMbusy(_mnox)
        if('Er:' in _rst1):
            rt = _rst1
            return(rt)

        _mnxl = self.Ctl_GetSelected('INTERNAL')
        if(_mnxl[0] == _mnox):
            rt = self.pm16c_Scan('A',_mnox,_mode)
        elif(_mnxl[1] == _mnox):
            rt = self.pm16c_Scan('B',_mnox,_mode)
        elif(_mnxl[2] == _mnox):
            rt = self.pm16c_Scan('C',_mnox,_mode)
        elif(_mnxl[3] == _mnox):
            rt = self.pm16c_Scan('D',_mnox,_mode)
        else:
            rt = _rt + ' Cannot be executed because it is not set to any channel.'
        return(rt)
        
    def Motor_GetJogPulse(self,mnx):
        _cksts6 = 'R\w\w\w\w\w\w'
        _mnox = mnx
        _rdata3 = []
        _rt = 'Er:'
        rt = 'Ok:'
        _cmd = 'S4' + _mnox + 'E'
        _rdata = self.device_act(_cmd)
        _ckr = re.match(_cksts6,_rdata)
        if(_ckr is None):
            rt = _rt + ' System error.'
        else:
            _rdatat = _rdata.lstrip('R')
            _rdata3 = tuple(_rdatat)
            _rdatac = _rdata3[0] + _rdata3[1] + _rdata3[2] + _rdata3[3]
            _rdatai = int(_rdatac,16)
            rt = str(_rdatai)
        return(rt)

    def Motor_SetJogPulse(self,mnx,sd):
        _mnox =mnx
        _sdata = sd
        _sdatat =[]
        _cmd = 'S5'
        _rt = 'Er:'
        rt = 'Ok:'

        _rlb = self.rolMbusy(_mnox)
        if('Er:' in _rlb):
            rt = _rlb
            return(rt)
        try:
            _sdatai = int(_sdata)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        if( (_sdatai < 1) or (_sdatai > 9999)):
            rt = _rt + ' Data out of range.'
            return(rt)
        _sdatax = format(_sdatai,'X')
        _sdataxt = _sdatax.zfill(4)
        _sdatat = tuple(_sdataxt)
        _cmd0 = _cmd + _mnox + 'E' + _sdatat[0] + _sdatat[1]
        self.device_send(_cmd0)
        time.sleep(WAIT_MEMWRITE)
        _cmd1 = _cmd + _mnox + 'F' + _sdatat[2] + _sdatat[3]
        self.device_send(_cmd1)
        time.sleep(WAIT_MEMWRITE)
        return(rt)

    def MotorX_ScanHome(self,mnx,md):
        _mnox =mnx
        _mode = md
        _mnxl = []
        _bsych = ''
        _rt = 'ER:'
        rt = 'Ok:'

        _rlb = self.rolMbusy(_mnox)
        if('Er:' in _rlb):
            rt = _rlb
            return(rt)
        _mnxl = self.Ctl_GetSelected('INTERNAL')
        if( _mnox == _mnxl[0]):
            _rsts = self.pm16cX_Scan('A',_mnox,_mode)
            return(_rsts)
        elif( _mnox == _mnxl[1]):
            _rsts = self.pm16cX_Scan('B',_mnox,_mode)
            return(_rsts)
        elif( _mnox == _mnxl[2]):
            _rsts = self.pm16cX_Scan('C',_mnox,_mode)
            return(_rsts)
        elif( _mnox == _mnxl[3]):
            _rsts = self.pm16cX_Scan('D',_mnox,_mode)
            return(_rsts)
        else:
            _bsych = self.Ctl_IsBusy('ALL')
            if('A:0' in _bsych):
                _setstsA = self.Ctl_Select('A',_mnox)
                if('Ok:' in _setstsA):
                    rt = self.pm16cX_Scan('A',_mnox,_mode)
                else:
                    rt = _rt + ' Processing failure.'
            elif('B:0' in _bsych):
                _setstsB = self.Ctl_Select('B',_mnox)
                if('Ok:' in _setstsB):
                    rt = self.pm16cX_Scan('B',_mnox,_mode)
                else:
                    rt = _rt + ' Processing failure.'
            elif('C:0' in _bsych):
                _setstsC = self.Ctl_Select('C',_mnox)
                if('Ok:' in _setstsC):
                    rt = self.pm16cX_Scan('C',_mnox,_mode)
                else:
                    rt = _rt + ' Processing failure.'
            elif('D:0' in _bsych):
                _setstsD = self.Ctl_Select('D',_mnox)
                if('Ok:' in _setstsD):
                    rt = self.pm16cX_Scan('D',_mnox,_mode)
                else:
                    rt = _rt + ' Processing failure.'
            else:
                rt = _rt + ' All channels are busy.'
        return(rt)

###################################################################
#   pm16c procedure
###################################################################
    def pm16c_disconnect(self):
        self.Ctl_Stop()
        rt = 'QuitControl'
        return(rt)

    def pm16c_code2speed(self,cd):
        _code = cd
        _spd = self._MotorSpeed[_code]
        return(_spd)

    def pm16cX_rate2code(self,spd):
        _spdf = spd
        _code = '0'
        for v in range(115):
            _tmpcf = float(self._AccelarationRate[v])
            if(_tmpcf <= _spdf):
                _code = str(v)
                break
        return(_code)

    def pm16c_speed2hexcode(self,sd):
        _speed = int(sd)
        _setv = -1
        _speedc = 'Er: The entered speed cannot be set'
        for v in range(188):
            _sspdi = int(self._MotorSpeed[v])
            if( _sspdi == _speed):
                _setv = v
                break
            elif( _sspdi > _speed):
                _setv = v - 1
                break
        if( _setv != -1):
            _speedct = format(_setv,'X')
            _speedc = _speedct.zfill(2)
        return(_speedc)
        
    def pm16c_getstatus(self,ch):
        _cksts2 = 'R\w\w'
        _ch = ch.upper()
        _cmd = ''
        _rt = 'Er:'
        if(_ch == 'A'):
            _cmd = 'S21'
        elif(_ch == 'B'):
            _cmd = 'S23'
        elif(_ch == 'C'):
            _cmd = 'S25'
        elif(_ch == 'D'):
            _cmd = 'S27'
        else:
            rt = _rt + ' Bad channel.'
            return(rt)
        _dsts = self.device_act(_cmd)
        _ckr = re.match(_cksts2,_dsts)
        if(_ckr is None):
            rt = _rt + ' Could not get setting motor number.'
            return(rt)
        _dstschi = _dsts.lstrip('R')
        rti = int(_dstschi,16)
        rt = _dstschi.zfill(2)
        return(rti)

    def pm16c_flushdata(self):
        global gb_Is_busyflg_A
        global gb_Is_busyflg_B
        global gb_Is_busyflg_C
        global gb_Is_busyflg_D
## temp ->
        _fbsy = [gb_Is_busyflg_A,gb_Is_busyflg_B,gb_Is_busyflg_C,gb_Is_busyflg_D]
## <- temp

#        global gb_Flg_remote
        rt = 'Ok:'

        _chmn = []
        _chmn = self.Ctl_GetSelected(chs = 'INTERNAL')      # get setting of motor number to channel
        _stsAt = self.pm16c_getstatus(ch = 'A')              # get status of the channel A
        _ckdAt = _stsAt & 0x01
        _ckdA = format(_ckdAt,'X')
        _ckA = _ckdA.zfill(2)
        if( _ckA == '01'):
            gb_Is_busyflg_A = _chmn[0]
        else:
            gb_Is_busyflg_A ='nE'
        _stsBt = self.pm16c_getstatus(ch = 'B')
        _ckdBt = _stsBt & 0x01
        _ckdB = format(_ckdBt,'X')
        _ckB = _ckdB.zfill(2)
        if( _ckB == '01'):
            gb_Is_busyflg_B = _chmn[1]
        else:
            gb_Is_busyflg_B = 'nE'
        _stsCt = self.pm16c_getstatus(ch = 'C')
#        _stsCt = int(_stsT,base=16)
        _ckdCt = _stsCt & 0x01
        _ckdC = format(_ckdCt,'X')
        _ckC = _ckdC.zfill(2)
        if( _ckC == '01'):
            gb_Is_busyflg_C = _chmn[2]
        else:
            gb_Is_busyflg_C = 'nE'
        _stsDt = self.pm16c_getstatus(ch = 'D')
#        _stsDt = int(_stsT,base=16)
        _ckdDt = _stsDt & 0x01
        _ckdD = format(_ckdDt,'X')
        _ckD = _ckdD.zfill(2)
        if( _ckD == '01'):
            gb_Is_busyflg_D = _chmn[3]
        else:
            gb_Is_busyflg_D = 'nE'
        _rt = self.Ctl_IsBusy()

        _destsendstr = 'System _ChangeCtlIsBusy ' + str(_rt)
        st.send(_destsendstr)
        _fbsy = [gb_Is_busyflg_A,gb_Is_busyflg_B,gb_Is_busyflg_C,gb_Is_busyflg_D]

        self.Ctl_GetFunction()

        rt = _rt + '.' + str(_fbsy)  # replay busyFlg & busy per channel
        return(rt)

    def pm16c_dec2hex(self,dd):
        _ddatai = dd
        if((_ddatai < -8388608) and (_ddatai > 8388607)):
            _rt = 'ER: Data out of range.'
        else:
            if(_ddatai < 0):
                _datct = (_ddatai+1)*(-1)
                _rt = _datct ^ 0xffffff
            else:
                _rt = _ddatai
        return(_rt)

    def pm16c_getm1byte(self,mnx,st):
        _cksts3 = 'R\w\w\w\w\w\w'
        _rt = 'Er:'
        _mnox = mnx
        _datan = st
        _cmd = 'S4' + _mnox + str(_datan)
        _rdt = self.device_act(_cmd)
        _ckr = re.match(_cksts3,_rdt)
        if(_ckr is None):
            rt = _rt + ' Could not get setting motor number.'
            return(rt)
        _rdtcki = _rdt.lstrip('R')
        rt = _rdtcki[:-4]
#        _rdt2 = int(_rdtcki,base=16)
        return(rt)

    def pm16c_getm3bytes(self,mn,st):
        global gb_pm16cx
        _motorN = mn
        _startK = st
        _pm16cx = gb_pm16cx
        _cksts6 = 'R\w\w\w\w\w\w'
        _cmd =''
        _rt = 'Er:'

        if((_pm16cx == 'on') and ((_startK == '3') or (_startK == '6'))):
            rt = self.pm16cX_GetCwCcwLs(_motorN,_startK)
            return(rt)
        elif((_pm16cx == 'on') and (_startK == '0')):
            rt = self.pm16cX_GetValue(_motorN,_startK)
            return(rt)
        else:
            try:
                 _mni = int(_motorN)
            except ValueError:
                rt = _rt + ' Bad Motor Number.'
                return(rt)
            if((_mni < 0) or (_mni > 15) ):
                rt = _rt + ' Bad Motor Number.'
                return(rt)
###
#        if(_mni == 0):
#            _mnx = '0'
#        else:
#            _mnx_tmp = hex(_mni).strip('0x')
#            _mnx = _mnx_tmp.upper()
        _mnx = format(_mni,'X')

        _cmd = 'S4' + str(_mnx) + _startK
        _dsts = self.device_act(_cmd)
        _ckr = re.match(_cksts6,_dsts)
        if(_ckr is None):
            rt = _rt + ' Bad read value.'
            return(rt)
        _dstschi = _dsts.lstrip('R')
        _dstsht = int(_dstschi,16)
#        _dstsh = hex(_dstsht)
        _dckk = _dstsht & 0x800000
        _dckkxt = format(_dckk,'X')
        _dckkx = _dckkxt.zfill(6)
        if(_dckkx == '800000'):
            _dstsht = (_dstsht ^ 0xffffff )*(-1)-1
        _rtt = format(_dstsht,'X')
#        rt = rtt.zfill(6)
        _rtti = int(_rtt,16)
        rt = str(_rtti)
        return(rt)

    def pm16c_setspeedcommon(self,mnx,sdt,spf):
        global gb_pm16cx
        _mnox = mnx
        _setdata = sdt
        _spf = spf
        pm16cx = gb_pm16cx
        _cmd = ''
        _rt = 'Er:'
        rt = 'Ok:'

        if((_spf != '9') and (_spf != 'A') and (_spf != 'B')):
            rt = _rt + ' Internal Error.'
            return(rt)
        if(pm16cx == 'on'):
            rt = self.pm16cX_setspeedcommon(_mnox,_setdata,_spf)
            return(rt)

        _rolb = self.rolMbusy(_mnox)
        if(('Er:' in _rolb)):
            rt = _rolb
            return(rt)

        _spdi = int(_setdata)
        if( _spdi < 0):
            _spdi = 0

        _spdx = self.pm16c_speed2hexcode(_spdi)
        if('Er:' in _spdx):
            rt = _spdx
            return(rt)
        _cmd = 'S5' + _mnox + _spf + _spdx
        self.device_send(_cmd)
        time.sleep(0.04)
        _rst1 = self.pm16c_getm1byte(_mnox,_spf)
        _rst1i = int(_rst1,16)
        _rst2 = self.pm16c_code2speed(_rst1i)
        _setspd = str(_rst2)
        rt = rt + ' Setting speed = ' + _setspd
        return(rt)

    def pm16c_getnow(self):
        _now = time.strftime('%Y/%m/%d %H:%M:%S')
        return(_now)

    def pm16c_Scan(self,ch,mnx,md):
        global gb_Is_busyflg_A
        global gb_Is_busyflg_B
        global gb_Is_busyflg_C
        global gb_Is_busyflg_D
        global gb_devicename
        global gb_cliant
        global gb_Interval_Time

        _devname = gb_devicename
        _chs = ch
        _mnox = mnx
        _mode = md
        _cmd = ''
        _rt = 'Er:'
        rt = 'Ok:'

        if(_chs == 'A'):
            _cmd = 'S30'
            gb_Is_busyflg_A = _mnox
        elif(_chs == 'B'):
            _cmd = 'S31'
            gb_Is_busyflg_B = _mnox
        elif(_chs == 'C'):
            _cmd = 'S38'
            gb_Is_busyflg_C = _mnox
        elif(_chs == 'D'):
            _cmd = 'S39'
            gb_Is_busyflg_D = _mnox
        else:
            rt = _rt + ' Bad channel.'
            return(rt)
        _cmd = _cmd + _mode

        _destsendstr =  str(_devname)  + '>System _ChangedIsBusy 1'
        st.send(_destsendstr)

        gb_Interval_Time = INTERVAL_RUN
        _bsts = self.Ctl_IsBusy()
        if(_bsts == '1'):
            _destsendstr =  str(_devname)  + '>System _ChangedIsBusy 1'
            st.send(_destsendstr)
        self.device_send(_cmd)
        return(rt)

    def pm16c_rate2hexcode(self,sd):
        _spd = sd
        _rt = 'Er: No corresponding rate value.'

        try:
            _spdi = int(_spd)
        except ValueError:
            rt = 'Er: Bad parameter.'
            return(rt)

        for v in range(20):
            _ratedi = int(self._MotorSpeedRate[v])
            if(_ratedi <= _spdi):
                _rateci = int(v)
                _ratex = format(_rateci,'X')
                _rtad = _ratex.zfill(2)
                _rt = 'Ok:'
                break
        if(_rt == 'Ok:'):
            rt = _rtad
        else:
            rt = _rt
        return(rt)

    def pm16c_code2rate(self,rd):
        _rcodei = int(rd)
        _rated = self._MotorSpeedRate[_rcodei]
        return(_rated)

##################################################################
#   pm16cX procedure
##################################################################

    def pm16cX_GetValue(self,mn,st):
        _motorN = mn
        _startK = st
        _cmd0 ='PS?'
        _rt = ''
        _mnoi = int(_motorN)
        if( (_mnoi < 0) or (_mnoi > 15) ):
            _rt = 'Er: Bad motor number'
            return(_rt)
        _motorNx = format(_mnoi,'X')
        _cmd = _cmd0 + str(_motorNx)
        _drd = self.device_act(_cmd)
        if( '+' in _drd):
            _drd = _drd.lstrip('+')
            _rt = _drd.lstrip('0')
        elif('-' in _drd):
            _drd = _drd.lstrip('-')
            _drdt = _drd.lstrip('0')
            _rt = '-' + _drdt

        if(_rt == ''):
            _rt = '0'
        rt = _rt
        return(rt)

    def pm16cX_GetCwCcwLs(self,mn,st):
        _motorN = int(mn)
        _mnx = ''
        _startK = st
        _start = ''
        _cmd = ''
        _rt = ''
        ## CHK-02 =>
        if((_motorN < 0) or (_motorN > 15)):
            _rt = 'Er: Bad motor number.'
            return(_rt)
        ## <- CHK-02
        if(_startK == '3'):
            _start = 'F'
        elif(_startK == '6'):
            _start = 'B'
        elif((_startK != 'F') and (_startK != 'B')):
            _rt = 'Er: Bad Internal'
            return(_rt)

        _mnx = format(_motorN,'X')

        _cmd = _start + 'L?' + str(_mnx)
        _rdt = self.device_act(_cmd)
        if( '+' in _rdt):
            _rdt = _rdt.lstrip('+')
            _rdt = _rdt.lstrip('0')
        else:
            _rdt = _rdt.lstrip('-')
            _rdt = _rdt.lstrip('0')
            _rdt = '-' + _rdt
        _rt =_rdt
        return(_rt)

    def pm16cX_GetSTS(self):
        _cmd ='STS?'
        rt = self.device_act(_cmd)
        return(rt)

    def pm16c_setm3bytes(self,mnx,sdi,scmd):
        global gb_pm16cx
        pm16cx = gb_pm16cx
        _mnox = mnx
        _setdatai = sdi
        _scmd = scmd
        _rt = 'Er:'
        if((pm16cx == 'on') and (_scmd == '3') or (_scmd == '6') ):
            rt = self.pm16cX_SetCwCcwLs(_mnox,_scmd,_setdatai)
            return(rt)
        elif((pm16cx == 'on') and (_scmd == '0')):
            rt = self.pm16cX_Preset(_mnox,_scmd,_setdatai)
            return(rt)

        _rolb = self.rolMbusy(_mnox)
        if('Er:' in _rolb):
            return(_rolb)

        _cmd = 'S5' + _mnox
        _radd = int(_scmd)
        _setdatax = format(_setdatai,'6X')
        _strsd = str(_setdatax)
        _stdt0 = _strsd[0] + _strsd[1]
        _stdt1 = _strsd[2] + _strsd[3]
        _stdt2 = _strsd[4] + _strsd[5]
        _cmd0 = _cmd + str(_radd) + _stdt0
        _cmd1 = _cmd + str(_radd+1) + _stdt1
        _cmd2 = _cmd + str(_radd+2) + _stdt2
        self.device_send(_cmd0)
        time.sleep(0.04)
        self.device_send(_cmd1)
        time.sleep(0.04)
        self.device_send(_cmd2)
        time.sleep(0.04)
        return('Ok:')

    def pm16cX_SetCwCcwLs(self,mn,sc,sdti):
        _mnox = mn
        _startcode = sc
        _datai = sdti
        _cmd = ''
        _rt = 'Er:'
        if((_datai < -2147483647) or (_datai > 2147483647)):
            _rt = _rt + ' Data out of range.'
        if(_startcode == '3'):
            _cmd = 'F'
        elif(_startcode == '6'):
            _cmd = 'B'
        else:
            _rt = _rt + ' Bad Internal ' + str(_startcode)
        _rol = self.Ctl_GetFunction()
        if( _rol == '0'):
            _rt = _rt + ' Offline.'
        _bst = self.Motor_IsBusy(_mnox)
        if( _bst == '1'):
            _rt = _rt + ' Busy.'
        if(' ' in _rt):
            return(_rt)
        _sdata = str(_datai)
#        if(_datai > 0):
#            _sdata = '+' + _sdata
        _cmd = _cmd + 'L' + _mnox + _sdata
        self.device_send(_cmd)
        time.sleep(0.04)
        return('Ok:')

    def pm16c_SetValue(self,ch,sd,mn,md):
        global gb_devicename
        global gb_pm16cx
        global gb_CancelBacklash
        global gb_Is_busyflg_A
        global gb_Is_busyflg_B
        global gb_Is_busyflg_C
        global gb_Is_busyflg_D
        global gb_Interval_Time

        devname = gb_devicename
        pm16cx = gb_pm16cx
        _cancelB = gb_CancelBacklash
        _ch = ch
        _data = sd
        _mn = mn
        _mode = md
        _currentV = ''
        _cmd = ''
        _rt = 'Er:'
        rt = 'Ok:'

        _ckdi = self.chkint(_data)
        if('Er:' in str(_ckdi)):     # _ckdi ; int-value or error message
            rt = _ckdi
            return(rt)
        _mni = int(_mn)
        _mnx = format(_mni,'X')
        if(pm16cx == 'on'):
            _rsts = self.pm16cX_SetValue(_ch,_ckdi,_mn,_mode)
            return(_rsts)
        if((_ch != 'A') and (_ch != 'B') and (_ch != 'C') and (_ch != 'D')):
            rt = _rt + ' Bad channel.'
        _currentV = self.Ctl_GetValue(_ch)
        _currentVi = int(_currentV)
        if(_mode == 'REL'):
            _relposi = _currentVi + _ckdi
            if((_relposi < -8388608) or (_relposi > 8388607)):
                rt = _rt + ' Data out of range.'
                return(rt)
            else:
                _absstpi = _ckdi
        else:               # mode == 'ABS'
            _absstpi = _ckdi
        if((int((_cancelB[_mni]))>0) and (_absstpi > _currentVi)):
            _scmd = 'B'
        elif((int(_cancelB[_mni])<0) and (_absstpi < _currentVi)):
            _scmd = 'B'
        else:
            _scmd = ''
        _ckdx = self.pm16c_dec2hex(_ckdi)
        _ckdx = str(format(_ckdx,'X'))
        _ckdx = _ckdx.zfill(6)
        if((_ch == 'A') and (_mode == 'ABS')):
            _cmd = 'S32' + _ckdx + '13' + _scmd
            gb_Is_busyflg_A = _mnx
        elif((_ch == 'B') and (_mode == 'ABS')):
            _cmd = 'S33' + _ckdx + '13' + _scmd
            gb_Is_busyflg_B = _mnx
        elif((_ch == 'C') and (_mode == 'ABS')):
            _cmd = 'S3A' + _ckdx + '13' + _scmd
            gb_Is_busyflg_C = _mnx
        elif((_ch == 'D') and (_mode == 'ABS')):
            _cmd = 'S3B' + _ckdx + '13' + _scmd
            gb_Is_busyflg_D = _mnx
        elif((_ch == 'A') and (_mode == 'REL')):
            _cmd = 'S32' + _ckdx + '12' + _scmd
            gb_Is_busyflg_A = _mnx
        elif((_ch == 'B') and (_mode == 'REL')):
            _cmd = 'S33' + _ckdx + '12' + _scmd
            gb_Is_busyflg_B = _mnx
        elif((_ch == 'C') and (_mode == 'REL')):
            _cmd = 'S3A' + _ckdx + '12' + _scmd
            gb_Is_busyflg_C = _mnx
        elif((_ch == 'D') and (_mode == 'REL')):
            _cmd = 'S3B' + _ckdx + '12' + _scmd
            gb_Is_busyflg_D = _mnx

###
        _destsendstr =  str(devname)  + '.' + str(self.num2name(_mnx)) + '>System _ChangedIsBusy 1'
        st.send(_destsendstr)
        if((gb_Is_busyflg_A != 'nE') and (gb_Is_busyflg_B != 'nE') and (gb_Is_busyflg_C != 'nE') and (gb_Is_busyflg_D != 'nE')):
            _destsendstr = 'System _ChangedCtlIsBusy 1'
            st.send(_destsendstr)
###
        gb_Interval_Time = INTERVAL_RUN
        self.device_send(_cmd)
        time.sleep(0.1)
        return(rt)

    def pm16cX_SetValue(self,ch,sdi,mn,md):
        global gb_devicename
        global gb_CancelBacklash
        global gb_Is_busyflg_A
        global gb_Is_busyflg_B
        global gb_Is_busyflg_C
        global gb_Is_busyflg_D
        global gb_Interval_Time

        devname = gb_devicename
        _cancelB = gb_CancelBacklash

        _ch = ch
        _dati = sdi
        _mno = mn
        _mode = md
        _cmd0 = ''
        _cmd1 = ''
        _cmd = ''
        _si = ''
        _rt = 'Er:'
        rt = 'Ok:'

        _mnoi = int(_mno)
        _mnox = format(_mnoi,'X')

        if((_ch != 'A') and (_ch != 'B') and (_ch != 'C') and (_ch != 'D')):
            rt = _rt + ' Bad channel.'
        if((_dati < -2147483647) or (_dati > 2147483647)):
            rt = _rt + ' Data out of range.'
            return(rt)
        _ckmno = self.Ctl_GetSelected(_ch)
        if(_mnox != _ckmno):
            rt = _rt + ' Bad Internal ' + _ch + ' ' + str(_mnox)
            return(rt)
        _currentV = self.pm16cX_GetValue(_mno,'0')
        _currentVi = int(_currentV)
        if(_mode == 'REL'):
            _cmd0 = 'REL'
        else:           # _mode = 'ABS'
            _cmd0 = 'ABS'
        _absstpi = _dati
        if(_absstpi >= 0):
            _si = '+'
        if((int(_cancelB[_mnoi])>0) and (_absstpi > _currentVi)):
            _cmd1 = 'B'
        elif((int(_cancelB[_mnoi])<0) and (_absstpi < _currentVi)):
            _cmd1 = 'B'
        else:
            _cmd1 = ''
        _sdatastr = str(_absstpi)
        _sdata = _sdatastr.zfill(10)
        if(_si == '+'):
            _sdatas = _si + str(_sdata)
        else:
            _sdatas = str(_sdata)
        _cmd = _cmd0 + _mnox + _cmd1 + _sdatas
        if(_ch == 'A'):
            gb_Is_busyflg_A = _mnox
        elif(_ch == 'B'):
            gb_Is_busyflg_B = _mnox
        elif(_ch == 'C'):
            gb_Is_busyflg_C = _mnox
        elif(_ch == 'D'):
            gb_Is_busyflg_D = _mnox
###
        _destsendstr =  str(devname)  + '.' + str(self.num2name(_mnox)) + '>System _ChangedIsBusy 1'
        st.send(_destsendstr)
        if((gb_Is_busyflg_A != 'nE') and (gb_Is_busyflg_B != 'nE') and (gb_Is_busyflg_C != 'nE') and (gb_Is_busyflg_D != 'nE')):
            _destsendstr = 'System _ChangedCtlIsBusy 1'
            st.send(_destsendstr)
###
        gb_Interval_Time = INTERVAL_RUN
        self.device_send(_cmd)
        time.sleep(0.1)
        return(rt)

    def pm16cX_getspeedcommon(self,mnx,spf):
        _mnox = mnx
        _spf = spf
        _scmd = ''
        _cmd = 'SPD'
        _rt = 'Er:'
        rt = ''
        if(_spf == '9'):
            _scmd = 'H?'
        elif(_spf == 'A'):
            _scmd = 'M?'
        elif(_spf == 'B'):
            _scmd = 'L?'
        elif((_spf == 'H') or (_spf == 'M') or (_spf == 'L')):
            _scmd = _spf + '?'
        else:
            rt = _rt + ' Bad Internal parameter. -> ' + _spf
            return(rt)
        _cmd = _cmd + _scmd + _mnox
        _rsts = self.device_act(_cmd)
        rt = _rsts.lstrip('0')
        return(rt)

    def pm16cX_setspeedcommon(self,mnx,sd,spf):
        _mnox = mnx
        _spdata = sd
        _spf = spf
        _scmd = ''
        _cmd = 'SPD'
        _rt = 'Er:'
        rt = 'Ok:'

        if(_spf == ''):
            rt = _rt + ' System error.'
            return(rt)
        try:
            _sdti = int(_spdata)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_sdti < 1) or (_sdti > 5000000)):
            rt = _rt + ' Data out of range.'
            return(rt)
        if(_spf == '9'):
            _scmd = 'H'
        elif(_spf == 'A'):
            _scmd = 'M'
        elif(_spf == 'B'):
            _scmd = 'L'
        elif((_spf == 'H') or (_spf == 'M') or (_spf == 'L')):
            _scmd = _spf
        else:
            rt = _rt + ' Bad Internal parameter. -> ' + _spf
            return(rt)

        _rol = self.Ctl_GetFunction()
        if(_rol == '0'):
            rt = _rt + ' Offline.'
            return(rt)
        _isbusy = self.Motor_IsBusy(_mnox)
        if(_isbusy == '1'):
            rt = _rt + ' Busy.'
            return(rt)
        _cmd = _cmd + _scmd + str(_mnox) + _spdata
        self.device_send(_cmd)
        return(rt)

    def pm16cX_Preset(self,mnx,cd,sd):
        _mnox =mnx
        _code = cd
        _sdata = sd
        _rt = 'Er:'
        rt = 'OK:'
        _cmd = ''

        try:
            _ckdi = int(_sdata)
        except ValueError:
            rt = _rt + ' Data out of range.'
            return(rt)
        if((_ckdi < -2147483647) or (_ckdi > 2147483647)):
            rt = _rt + ' Data out of range.'
            return(rt)
        else:
            if(_ckdi >= 0):
                _sdata = '+' + _sdata
        _sts = self.rolMbusy(_mnox)
        if('Er:' in _sts):
            rt = _sts
            return(rt)
        _cmd = 'PS' + _mnox + _sdata
        self.device_send(_cmd)
        return(rt)
        
    def pm16cX_Scan(self,ch,mnx,md):
        global gb_Is_busyflg_A
        global gb_Is_busyflg_B
        global gb_Is_busyflg_C
        global gb_Is_busyflg_D
        global gb_devicename
        global gb_Interval_Time
        _devname = gb_devicename

        _chs = ch
        _mnox = mnx
        _mode = md
        _rt = 'Er:'
        rt = 'Ok:'

        if(_chs == 'A'):
            gb_Is_busyflg_A = _mnox
        elif(_chs == 'B'):
            gb_Is_busyflg_B = _mnox
        elif(_chs == 'C'):
            gb_Is_busyflg_C = _mnox
        elif(_chs == 'D'):
            gb_Is_busyflg_D = _mnox
        else:
            rt = _rt + ' Bad channel.'
            return(rt)
        if((_mode != 'FD') and (_mode != 'GT')):
            rt = _rt + ' Bad Internal ' + _mode
            return(rt)
        
        _destsendstr =  str(_devname)  + '>System _ChangedIsBusy 1'
        st.send(_destsendstr)

        gb_Interval_Time = INTERVAL_RUN

        _sts = self.Ctl_IsBusy()
        if(_sts == '1'):
            _destsendstr =  str(_devname)  + '>System _ChangedCtlIsBusy 1'
            st.send(_destsendstr)
        
        _cmd = _mode + 'HP' + _mnox
        self.device_send(_cmd)
        return(rt)


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
        lc_deviceComSTARSCommand = {}
        lc_deviceCTLSTARSCommand = {}
        lc_deviceMOTSTARSCommand = {}
        lc_deviceXCTLSTARSCommand = {}
        lc_deviceXMOTSTARSCommand = {}
        lc_MotorSpeed = []
        lc_MotorSpeedRate = []
        lc_AccelarationRate = []
###############################################
#          << Common Command >>    #          #
#---------------------------------------------#
        lc_deviceComSTARSCommand['GetAccRateList']                         ={"Target":"Common","Usage":"GetAccRateList","help":"Get list of settable motor acceleration rate."}
        lc_deviceComSTARSCommand['GetSpeedList']                           ={"Target":"Common","Usage":"GetSpeedList","help":"Get list of settable motor speed."}
        lc_deviceComSTARSCommand['getversion']                             ={"Target":"Common","Usage":"getversion","help":"Return this program version."}
        lc_deviceComSTARSCommand['hello']                                  ={"Target":"Common","Usage":"hello","help":"The client returns \@hello nice to meet you.\""}
###############################################
#         << Standard Event Command >>        #
#---------------------------------------------#
        lc_deviceComSTARSCommand['_ChangedIsBusy']                         ={"Target":"Event", "help":"_ChangedIsBusy event shows that the status of motor has been changed. 1 is busy, 0 is free."}
        lc_deviceComSTARSCommand['_ChangedCtlIsBusy']                      ={"Target":"Event", "help":"_ChangedIsBusy event shows that the status of motor has been changed. 1 is busy, 0 is free."}
        lc_deviceComSTARSCommand['_ChangedValue']                          ={"Target":"Event", "help":"_ChangedValue event shows that the position of motor has been changed."}
        lc_deviceComSTARSCommand['_ChangedFunction']                       ={"Target":"Event", "help":"_ChangedFunction event event shows that the function has been changed. 1 is Remote, 0 is Local."}
###############################################
#      << Standard Controller Command >>      #
#---------------------------------------------#
        lc_deviceCTLSTARSCommand['GetCtlIsBusy']                           ={"Target":"Controller","Usage":"GetCtlIsBusy","help":"Check, is controller busy?"}
        lc_deviceCTLSTARSCommand['IsBusy']                                 ={"Target":"Controller","Usage":"IsBusy","help":"Check, is motor busy?"}
        lc_deviceCTLSTARSCommand['GetAccRateCode']                         ={"Target":"Controller","Usage":"GetAccRateCode","help":"Get acceleration rate code of \"MotorNumber\" (0 to 16)."}
        lc_deviceCTLSTARSCommand['GetAccRate']                             ={"Target":"Controller","Usage":"GetAccRate","help":"Get acceleration rate of \"MotorNumber\" (0 to 16)."}
        lc_deviceCTLSTARSCommand['flushdata']                              ={"Target":"Controller","Usage":"flushdata","help":"Get all status of PM16C-04 and sends event messages to System."}
        lc_deviceCTLSTARSCommand['flushdatatome']                          ={"Target":"Controller","Usage":"flushdatatome","help":"Get all status of PM16C-04 and sends event messages to me."	}
        lc_deviceCTLSTARSCommand['GetCancelBacklash']                      ={"Target":"Controller","Usage":"GetCancelBacklash MotorNumber","help":"Get cancel backlash of \"MotorNumber\" (0 to 16)."}
        lc_deviceCTLSTARSCommand['GetDigitalCcwLs']                        ={"Target":"Controller","Usage":"GetDigitalCcwLs","help":"Get CCW software limit switch (DIGITAL LS) of \"MotorNumber\" (0 to 16)."}
        lc_deviceCTLSTARSCommand['GetDigitalCwLs']                         ={"Target":"Controller","Usage":"GetDigitalCwLs","help":"Get CW software limit switch (DIGITAL LS) of MotorNumber (0 to 16)."}
        lc_deviceCTLSTARSCommand['GetRomVersion']                          ={"Target":"Controller","Usage":"GetRomVersion","help":"Get firmware virsion of PM16C-04."}	
        lc_deviceCTLSTARSCommand['GetFunction']                            ={"Target":"Controller","Usage":"GetFunction","help":"Get function \"1=Remote/0=Local\"."}
        lc_deviceCTLSTARSCommand['GetHighSpeed']                           ={"Target":"Controller","Usage":"GetHighSpeed","help":"Get high speed value of \"MotorNumber\" (0 to 16)."}
        lc_deviceCTLSTARSCommand['GetJogPulse']                            ={"Target":"Controller","Usage":"GetJogPulse","help":"Get jog pulse value of \"MotorNumber\" (0 to 16)."}
        lc_deviceCTLSTARSCommand['GetFunctionStatus']                      ={"Target":"Controller","Usage":"GetFunctionStatus","help":"Get limit switch and \"remote/local\" status on channel A and B.   bit0 : C POS CW LS,  bit1 : C POS CCW LS,  bt2 : C POS Z. LS,  bit4 : D POS CW LS,  bit5 : D POS CCW LS,  bit6 : D POS Z. LS,  bit8 : A POS CW LS,  bit9 : A POS CCW LS,  bitA : A POS Z. LS,  bitB : STATUS CPU/MANU,  bitC : B POS CW LS,  bitD : B POS CCW LS,  bitE : B POS Z. LS."}
        lc_deviceCTLSTARSCommand['GetLimits']                              ={"Target":"Controller","Usage":"GetLimits","help":"Get limit switches value of \"MotorNumber\" (0 to 16) in register. bit0 : CW LS A/B,  bit1 : CCW LS A/B,  bit2 : Z LS A/B,  bit3 : CW LS ENABLE,  bit4 : CCW LS ENABLE,  bit5 : DIGITAL LS ENABLE,   bit6 : HOLD,  bit7 : MOTOR OFF."}
        lc_deviceCTLSTARSCommand['GetLowSpeed']                            ={"Target":"Controller","Usage":"GetLowSpeed","help":"Get low speed value of \"MotorNumber\" (0 to 16)."}
        lc_deviceCTLSTARSCommand['GetMiddleSpeed']                         ={"Target":"Controller","Usage":"GetMiddleSpeed","help":"Get middle speed value of \"MotorNumber\" (0 to 16)."}
        lc_deviceCTLSTARSCommand['GetMotorName']                           ={"Target":"Controller","Usage":"GetMotorName","help":"Get motor name of \"MotorNumber\"."}
        lc_deviceCTLSTARSCommand['GetMotorNumber']                         ={"Target":"Controller","Usage":"GetMotorNumber","help":"Get motor number of \"MotorName\"."}
        lc_deviceCTLSTARSCommand['GetValue']                               ={"Target":"Controller","Usage":"GetValue","help":"Get postion data of \"Channle\" (A, B, C, D) or \"MotorNumber\" (0 to 16)."}
        lc_deviceCTLSTARSCommand['GetSelected']                            ={"Target":"Controller","Usage":"GetSelected","help":"Get selected channel (A, B, C, D or N = not selected) with MotorName or \"MotorNumber\" (0 to 16) or get selected motor number with Channel (A, B, C, D)."}
        lc_deviceCTLSTARSCommand['GetStatus']                              ={"Target":"Controller","Usage":"GetStatus","help":"Get status register value of Channel (A, B, C, D).    bit0: BUSY,  bit1 : DRIVE,  bit2 : not used,  bit3 : not used,  bit4 : COMERR,  bit5 : LDEND, bit6 : SSEND,  bit7 : ESEND."}
        lc_deviceCTLSTARSCommand['GetMotorList']                           ={"Target":"Controller","Usage":"GetMotorList","help":"List motor names."}
        lc_deviceCTLSTARSCommand['StopEmergency']                          ={"Target":"Controller","Usage":"StopEmergency [Channel|MotorNumber]","help":"Make a sudden stop which shown \"Channel\" or \"MotorNumber\". If they are not specified, all motors will be stopped."}
        lc_deviceCTLSTARSCommand['ScanCcwConst']                           ={"Target":"Controller","Usage":"ScanCcwConst Channel|MotorNumber","help":"Move \"Channel\" (A, B, C, D) or \"MotorNumber\" (0 to 16) to \"CCW\" with constant scan mode."}
        lc_deviceCTLSTARSCommand['ScanCwConst']                            ={"Target":"Controller","Usage":"ScanCwConst Channel|MotorNumber","help":"Move \"Channel\" (A, B, C, D) or \"MotorNumber\" (0 to 16) to \"CW\" with constant scan mode."}
        lc_deviceCTLSTARSCommand['ScanCw']                                 ={"Target":"Controller","Usage":"ScanCw Channel|MotorNumber","help":"Move \"Channel\" (A, B, C, D) or \"MotorNumber\" (0 to 16) to \"CW\" with scan mode."}
        lc_deviceCTLSTARSCommand['ScanCcwHome']                            ={"Target":"Controller","Usage":"ScanCcwHome Channel|MotorNumber","help":"Move \"Channel\" (A, B, C, D) or \"MotorNumber\" (0 to 16) to \"CCW\" for finding home position."}
        lc_deviceCTLSTARSCommand['ScanCcw']                                ={"Target":"Controller","Usage":"ScanCcw Channel|MotorNumber","help":"Move \"Channel\" (A, B, C, D) or \"MotorNumber\" (0 to 16) to \"CCW\" with scan mode."}
        lc_deviceCTLSTARSCommand['ScanCwHome']                             ={"Target":"Controller","Usage":"ScanCwHome Channel|MotorNumber","help":"Move \"Channel\" (A, B, C, D) or \"MotorNumber\" (0 to 16) to \"CW\" for finding home position."}
        lc_deviceCTLSTARSCommand['SetValue']                               ={"Target":"Controller","Usage":"SetValue Channel|MotorNumber Value","help":"Move motor which is shown \"MotorNumber\" or \"Channel\" to \"Value\" absolutely."}
        lc_deviceCTLSTARSCommand['SetValueREL']                            ={"Target":"Controller","Usage":"SetValueREL Channel|MotorNumber Value","help":"Move motor which is shown \"MotorNumber\" or \"Channel\" to \"Value\" relatively."}
        lc_deviceCTLSTARSCommand['Select']                                 ={"Target":"Controller","Usage":"Select Channel MotorNumber","help":"Select MotorName or \"MotorNumber\" (0 to 16) on Channel (A, B, C, D)."}
        lc_deviceCTLSTARSCommand['JogCcw']                                 ={"Target":"Controller","Usage":"JogCcw","help":"Send CCW jog command to \"Channel\" (A, B, C, D) or \"MotorNumber\" (0 to 16)."}
        lc_deviceCTLSTARSCommand['JogCw']                                  ={"Target":"Controller","Usage":"JogCw Channel|MotorNumber","help":"Send CW jog command to \"Channel\" (A, B, C, D) or \"MotorNumber\" (0 to 16)."}
        lc_deviceCTLSTARSCommand['SetAccRate']                             ={"Target":"Controller","Usage":"SetAccRate MotorNumber Value","help":"Set acceleration rate of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceCTLSTARSCommand['SetCancelBacklash']                      ={"Target":"Controller","Usage":"SetCancelBacklash MotorNumber Value","help":"Set cancel backlash value of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceCTLSTARSCommand['SetDigitalCcwLs']                        ={"Target":"Controller","Usage":"SetDigitalCcwLs MotorNumber Value","help":"Set CCW software limit switch (DIGITAL LS) of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceCTLSTARSCommand['SetDigitalCwLs']                         ={"Target":"Controller","Usage":"SetDigitalCwLs MotorNumber Value","help":"Set CW software limit switch (DIGITAL LS) of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceCTLSTARSCommand['SetFunction']                            ={"Target":"Controller","Usage":"SetFunction 1|0","help":"Set function (Remote=1, Local=0)."}
        lc_deviceCTLSTARSCommand['Local']                                  ={"Target":"Controller","Usage":"Local","help":"Set function to \"Local\". (Same as SetFunction 0)."}
        lc_deviceCTLSTARSCommand['Remote']                                 ={"Target":"Controller","Usage":"Remote","help":"Set function to \"Remote\". (Same as SetFunction 1)."}
        lc_deviceCTLSTARSCommand['SetHighSpeed']                           ={"Target":"Controller","Usage":"SetHighSpeed MotorNumber Value","help":"Set high speed of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceCTLSTARSCommand['SetHold Channel']                        ={"Target":"Controller","Usage":"SetHold Channel 1|0","help":"Set hold (=1) or free (=0) motor on \"Channel\" (A, B, C, D)."}
        lc_deviceCTLSTARSCommand['SetJogPulse']                            ={"Target":"Controller","Usage":"SetJogPulse MotorNumber Value","help":"Set jog pulse value of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceCTLSTARSCommand['SetLimits']                              ={"Target":"Controller","Usage":"SetLimits MotorNumber Value","help":"Set limit switches value of \"MotorNumber\" (0 to 16) into \"Value\".   bit0 : CW LS A/B,  bit1 : CCW LS A/B,  bit2 : Z LS A/B,  bit3 : CW LS ENABLE,  bit4: CCW LS ENABLE,  bit5 : DIGITAL LS ENABLE, bit6 : HOLD,  bit7 : MOTOR OFF."}
        lc_deviceCTLSTARSCommand['SetLowSpeed']                            ={"Target":"Controller","Usage":"SetLowSpeed MotorNumber Value","help":"Set low speed of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceCTLSTARSCommand['SetMiddleSpeed ']                        ={"Target":"Controller","Usage":"SetMiddleSpeed MotorNumber Value","help":"Set middle speed of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceCTLSTARSCommand['Preset']                                 ={"Target":"Controller","Usage":"Preset MotorNumber Value","help":"Set motor position data of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceCTLSTARSCommand['SpeedHigh']                              ={"Target":"Controller","Usage":"SpeedHigh","help":"Set speed to \"High\"."}
        lc_deviceCTLSTARSCommand['SpeedLow']                               ={"Target":"Controller","Usage":"SpeedLow","help":"Set speed to \"Low\"."}
        lc_deviceCTLSTARSCommand['SpeedMiddle']                            ={"Target":"Controller","Usage":"SpeedMiddle","help":"Set speed to Middl."}
        lc_deviceCTLSTARSCommand['Standby']                                ={"Target":"Controller","Usage":"Standby","help":"Standby motor(s). The \"Standby\" command is used for starting 2 motors at the same time with SyncRun command."}
        lc_deviceCTLSTARSCommand['SyncRun']                                ={"Target":"Controller","Usage":"SyncRun","help":"Start motor(s). The \"SyncRun\" command is used for starting 2 motors at the same time with \"Standby\" command."}
        lc_deviceCTLSTARSCommand['Stop']                                   ={"Target":"Controller","Usage":"Stop [Channel|MotorNumber]","help":"Stop motors(s) which shown \"Channel\" or \"MotorNumber\". If they are not specified, all motors will be stopped."}
###############################################
#         << Standard Motor Command >>        #
#---------------------------------------------#
        lc_deviceMOTSTARSCommand['IsBusy']                                 ={"Target":"Motor","Usage":"IsBusy","help":"Check, is motor busy?"}
        lc_deviceMOTSTARSCommand['GetAccRateCode']                         ={"Target":"Motor","Usage":"GetAccRateCode","help":"Get acceleration rate code."}
        lc_deviceMOTSTARSCommand['GetAccRate']                             ={"Target":"Motor","Usage":"GetAccRate","help":"Get acceleration rate."}
        lc_deviceMOTSTARSCommand['GetCancelBacklash']                      ={"Target":"Motor","Usage":"GetCancelBacklash","help":"Get cancel backlash."}
        lc_deviceMOTSTARSCommand['GetDigitalCcwLs']                        ={"Target":"Motor","Usage":"GetDigitalCcwLs","help":"Get CCW software limit switch (DIGITAL LS)."}
        lc_deviceMOTSTARSCommand['GetDigitalCwLs']                         ={"Target":"Motor","Usage":"GetDigitalCwLs","help":"Get CW software limit switch (DIGITAL LS)."}
        lc_deviceMOTSTARSCommand['GetHighSpeed']                           ={"Target":"Motor","Usage":"GetHighSpeed","help":"Get high speed value."}
        lc_deviceMOTSTARSCommand['GetJogPulse']                            ={"Target":"Motor","Usage":"GetJogPulse","help":"Get jog pulse value."}
        lc_deviceMOTSTARSCommand['GetLimits']                              ={"Target":"Motor","Usage":"GetLimits","help":"Get limit switches value in register.  bit0 : CW LS A/B,  bit1 : CCW LS A/B,  bit2 : Z LS A/B,  bit3 : CW LS ENABLE,  bit4 : CCW LS ENABLE,  bit5 : DIGITAL LS ENABLE,  bit6 : HOLD,  bit7: MOTOR OFF."}
        lc_deviceMOTSTARSCommand['GetLowSpeed']                            ={"Target":"Motor","Usage":"GetLowSpeed","help":"Get low speed value of MotorName or \"MotorNumber\" (0 to 16)."}
        lc_deviceMOTSTARSCommand['GetMiddleSpeed']                         ={"Target":"Motor","Usage":"GetMiddleSpeed","help":"Get middle speed value."}
        lc_deviceMOTSTARSCommand['GetMotorNumber']                         ={"Target":"Motor","Usage":"GetMotorNumber","help":"Get motor number of motorname."}
        lc_deviceMOTSTARSCommand['GetValue']                               ={"Target":"Motor","Usage":"GetValue","help":"Get postion data."}
        lc_deviceMOTSTARSCommand['GetSelected']                            ={"Target":"Motor","Usage":"GetSelected","help":"Get selected channel (A, B, C, D or N = not selected)."}
        lc_deviceMOTSTARSCommand['StopEmergency']                          ={"Target":"Motor","Usage":"StopEmergency","help":"Make a sudden stop."}
        lc_deviceMOTSTARSCommand['ScanCcw']                                ={"Target":"Motor","Usage":"ScanCcw","help":"Move \"CCW\" direction with scan mode."}
        lc_deviceMOTSTARSCommand['ScanCwHome']                             ={"Target":"Motor","Usage":"ScanCwHome","help":"Move \"CW\" direction for finding home position."}
        lc_deviceMOTSTARSCommand['ScanCwConst']                            ={"Target":"Motor","Usage":"ScanCwConst","help":"Move \"CW\" direction with constant scan mode."}
        lc_deviceMOTSTARSCommand['ScanCw']                                 ={"Target":"Motor","Usage":"ScanCw","help":"Move \"CW\" direction with scan mode."}
        lc_deviceMOTSTARSCommand['ScanCcwHome']                            ={"Target":"Motor","Usage":"ScanCcwHome","help":"Move \"CCW\" direction for finding home position."}
        lc_deviceMOTSTARSCommand['ScanCcwConst']                           ={"Target":"Motor","Usage":"ScanCcwConst","help":"Move \"CCW\" direction with constant scan mode."}
        lc_deviceMOTSTARSCommand['SetValue']                               ={"Target":"Motor","Usage":"SetValue Value","help":"Move motor to \"Value\" absolutely."}
        lc_deviceMOTSTARSCommand['SetValueREL']                            ={"Target":"Motor","Usage":"SetValueREL Value","help":"Move motor to \"Value\" relatively."}
        lc_deviceMOTSTARSCommand['JogCcw']                                 ={"Target":"Motor","Usage":"JogCcw","help":"Send CCW jog command."}
        lc_deviceMOTSTARSCommand['JogCw']                                  ={"Target":"Motor","Usage":"JogCw","help":"Send CW jog command."}
        lc_deviceMOTSTARSCommand['SetAccRate']                             ={"Target":"Motor","Usage":"SetAccRate Value","help":"Set acceleration rate into \"Value\"."}
        lc_deviceMOTSTARSCommand['SetCancelBacklash']                      ={"Target":"Motor","Usage":"SetCancelBacklash Value","help":"Set cancel backlash value into \"Value\"."}
        lc_deviceMOTSTARSCommand['SetDigitalCcwLs']                        ={"Target":"Motor","Usage":"SetDigitalCcwLs Value","help":"Set CCW software limit switch (DIGITAL LS) into \"Value\"."}
        lc_deviceMOTSTARSCommand['SetDigitalCwLs']                         ={"Target":"Motor","Usage":"SetDigitalCwLs Value","help":"Set CW software limit switch (DIGITAL LS) into \"Value\"."}
        lc_deviceMOTSTARSCommand['SetHighSpeed']                           ={"Target":"Motor","Usage":"SetHighSpeed Value","help":"Set high speed into \"Value\"."}
        lc_deviceMOTSTARSCommand['SetJogPulse']                            ={"Target":"Motor","Usage":"SetJogPulse Value","help":"Set jog pulse value into \"Value\"."}
        lc_deviceMOTSTARSCommand['SetLimits']                              ={"Target":"Motor","Usage":"SetLimits Value","help":"Set limit switches value into \"Value\"."}
        lc_deviceMOTSTARSCommand['SetLowSpeed']                            ={"Target":"Motor","Usage":"SetLowSpeed Value","help":"Set low speed into \"Value\"."}
        lc_deviceMOTSTARSCommand['SetMiddleSpeed']                         ={"Target":"Motor","Usage":"SetMiddleSpeed Value","help":"Set middle speed into \"Value\"."}
        lc_deviceMOTSTARSCommand['Preset Value']                           ={"Target":"Motor","Usage":"Preset Value","help":"Set motor position data into \"Value\"."}
        lc_deviceMOTSTARSCommand['Stop']                                   ={"Target":"Motor","Usage":"Stop","help":"Stop motor."}
###############################################
#  << PM16CX additional Controller Command >> #
#---------------------------------------------#
        lc_deviceXCTLSTARSCommand['DrawLine']                              ={"Target":"Controller","Usage":" DrawLine [ChannelSet] MotorNumberX MotorNumberY EndValueX EndValueY","help":" Draw straight line, using \"ChannelSet\" ({AB or 0} or {CD or 1}) by moving \"MotorNumberX\" (0 to 16) from it's current to absolute \"EndValueX\", and \"MotorNumberY\" (0 to 16) from it's current to absolute \"EndValueY\". \"ChannelSet\" can be omitted to be selected automatically."}
        lc_deviceXCTLSTARSCommand['DrawLineREL']                           ={"Target":"Controller","Usage":" DrawLineREL [ChannelSet] MotorNumberX MotorNumberY ValueX ValueY","help":" Draw straight line, using \"ChannelSet\" ({AB or 0} or {CD or 1}) by moving \"MotorNumberX\" (0 to 16) from it's current to relative \"ValueX\", and \"MotorNumberY\" (0 to 16) from it's current to relative \"ValueY\". \"ChannelSet\" can be omitted to be selected automatically."}
        lc_deviceXCTLSTARSCommand['DrawCircularCw']                        ={"Target":"Controller","Usage":" DrawCircularCw [ChannelSet] MotorNumberX MotorNumberY EndValueX EndValueY CenterValueX CenterValueY","help":" Draw cw direction circlular with absolute center position data(\"CenterValueX\", \"CenterValueY\"), using \"ChannelSet\" ({AB or 0} or {CD or 1}) by moving \"MotorNumberX\" (0 to 16) from it's current to absolute \"EndValueX\", and \"MotorNumberY\" (0 to 16) from it's current to absolute \"EndValueY\". \"ChannelSet\" can be omitted to be selected automatically."}
        lc_deviceXCTLSTARSCommand['DrawCircularCwREL']                     ={"Target":"Controller","Usage":" DrawCircularCwREL [ChannelSet] MotorNumberX MotorNumberY EndValueX EndValueY CenterValueX CenterValueY","help":" Draw cw direction circlular with relative center position data(\"CenterValueX\", \"CenterValueY\"), using \"ChannelSet\" ({AB or 0} or {CD or 1}) by moving \"MotorNumberX\" (0 to 16) from it's current to relative \"EndValueX\", and \"MotorNumberY\" (0 to 16) from it's current to relative \"EndValueY\". \"ChannelSet\" can be omitted to be selected automatically."}
        lc_deviceXCTLSTARSCommand['DrawCircularCcw']                       ={"Target":"Controller","Usage":" DrawCircularCcw [ChannelSet] MotorNumberX MotorNumberY EndValueX EndValueY CenterValueX CenterValueY","help":" Draw ccw direction circlular with absolute center position data(\"CenterValueX\", \"CenterValueY\"), using \"ChannelSet\" ({AB or 0} or {CD or 1}) by moving \"MotorNumberX\" (0 to 16) from it's current to absolute \"EndValueX\", and \"MotorNumberY\" (0 to 16) from it's current to absolute \"EndValueY\". \"ChannelSet\" can be omitted to be selected automatically."}
        lc_deviceXCTLSTARSCommand['DrawCircularCcwREL']                    ={"Target":"Controller","Usage":" DrawCircularCcwREL [ChannelSet] MotorNumberX MotorNumberY EndValueX EndValueY CenterValueX CenterValueY","help":" Draw ccw direction circlular with relative center position data(\"CenterValueX\", \"CenterValueY\"), using \"ChannelSet\" ({AB or 0} or {CD or 1}) by moving \"MotorNumberX\" (0 to 16) from it's current to relative \"EndValueX\", and \"MotorNumberY\" (0 to 16) from it's current to relative \"EndValueY\". \"ChannelSet\" can be omitted to be selected automatically."}
        lc_deviceXCTLSTARSCommand['DrawArc']                               ={"Target":"Controller","Usage":" DrawArc [ChannelSet] MotorNumberX MotorNumberY EndValueX EndValueY ByPassPointX ByPassPointY","help":" Draw arc using \"ChannelSet\" ({AB or 0} or {CD or 1}) by moving \"MotorNumberX\" (0 to 16) from it's current to absolute \"EndValueX\" passing by absolute \"ByPassPointX\", and \"MotorNumberY\" (0 to 16) from it's current to absolute \"EndValueY\" passing by absolute \"ByPassPointY\". \"ChannelSet\" can be omitted to be selected automatically."}
        lc_deviceXCTLSTARSCommand['DrawArcREL']                            ={"Target":"Controller","Usage":" DrawArcREL [ChannelSet] MotorNumberX MotorNumberY EndValueX EndValueY ByPassPointX ByPassPointY","help":" Draw arc using \"ChannelSet\" ({AB or 0} or {CD or 1}) by moving \"MotorNumberX\" (0 to 16) from it's current to relative \"EndValueX\" passing by relative \"ByPassPointX\", and \"MotorNumberY\" (0 to 16) from it's current to relative \"EndValueY\" passing by relative \"ByPassPointY\". \"ChannelSet\" can be omitted to be selected automatically."}
        lc_deviceXCTLSTARSCommand['DrawCircle']                            ={"Target":"Controller","Usage":" DrawCircle [ChannelSet] MotorNumberX MotorNumberY ByPassPointX1 ByPassPointY1 ByPassPointX2 ByPassPointY2","help":" Draw arc using \"ChannelSet\" ({AB or 0} or {CD or 1}) by moving \"MotorNumberX\" (0 to 16) from it's current to current passing by absolute \"ByPassPointX1\" and \"ByPassPointX2\", and \"MotorNumberY\" (0 to 16) from it's current passing by absolute \"ByPassPointY1\" and \"ByPassPointY2\". \"ChannelSet\" can be omitted to be selected automatically."}
        lc_deviceXCTLSTARSCommand['DrawCircleREL']                         ={"Target":"Controller","Usage":" DrawCircleREL [ChannelSet] MotorNumberX MotorNumberY ByPassPointX1 ByPassPointY1 ByPassPointX2 ByPassPointY2","help":" Draw arc using \"ChannelSet\" ({AB or 0} or {CD or 1}) by moving \"MotorNumberX\" (0 to 16) from it's current to current passing by relative \"ByPassPointX1\" and \"ByPassPointX2\", and \"MotorNumberY\" (0 to 16) from it's current passing by relative \"ByPassPointY1\" and \"ByPassPointY2\". \"ChannelSet\" can be omitted to be selected automatically."}
        lc_deviceXCTLSTARSCommand['SpeedLow']                              ={"Target":"Controller","Usage":" SpeedLow [MotorNumber]","help":" Set speed to \"Low\" to \"MotorNumber\" (0 to 16). If it's not specified, all motors will be set to \"Low\"."}
        lc_deviceXCTLSTARSCommand['SpeedMiddle']                           ={"Target":"Controller","Usage":" SpeedMiddle [MotorNumber]","help":" Set speed to \"Middle\" to \"MotorNumber\" (0 to 16). If it's not specified, all motors will be set to \"Middle\"."}
        lc_deviceXCTLSTARSCommand['SpeedHigh']                             ={"Target":"Controller","Usage":" SpeedHigh [MotorNumber]","help":" Set speed to \"High\" to \"MotorNumber\" (0 to 16). If it's not specified, all motors will be set to \"High\"."}
        lc_deviceXCTLSTARSCommand['GetSpeedSelected']                      ={"Target":"Controller","Usage":" GetSpeedSelected MotorNumber","help":" Return selected speed (\"H\" (high), \"M\" (middle), \"L\" (low)) of \"MotorNumber\" (0 to 16)."}
        lc_deviceXCTLSTARSCommand['SetSpeedCurrent']                       ={"Target":"Controller","Usage":" SetSpeedCurrent MotorNumber SpeedValue","help":" Change speed to \"SpeedValue\" of \"MotorNumber\" (0 to 16) only while motor running."}
        lc_deviceXCTLSTARSCommand['SetTimingOutMode']                      ={"Target":"Controller","Usage":" SetTimingOutMode MotorNumber Value","help":" Set timing out mode value of \"MotorNumber\" (0 to 16) into \"Value\". Value 0: disable, 1: TTL gate , 2: TTL interval 200ns 3: TTL interval 10us 4: TTL interval 100us, 5: TTL interval 1ms"}
        lc_deviceXCTLSTARSCommand['SetTimingOutStart']                     ={"Target":"Controller","Usage":" SetTimingOutStart MotorNumber Value","help":" Set timing out start position value of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceXCTLSTARSCommand['SetTimingOutEnd']                       ={"Target":"Controller","Usage":" SetTimingOutEnd MotorNumber Value","help":" Set timing out end position value of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceXCTLSTARSCommand['SetTimingOutInterval']                  ={"Target":"Controller","Usage":" SetTimingOutInterval MotorNumber Value","help":" Set timing out interval value of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceXCTLSTARSCommand['SetTimingOutReady']                     ={"Target":"Controller","Usage":" SetTimingOutReady MotorNumber 1|0","help":" Set timing out ready (set=1, clear=0) of \"MotorNumber\" (0 to 16)."}
        lc_deviceXCTLSTARSCommand['GetTimingOutMode']                      ={"Target":"Controller","Usage":" GetTimingOutMode MotorNumber","help":" Return timing out mode value of \"MotorNumber\" (0 to 16)."}
        lc_deviceXCTLSTARSCommand['GetTimingOutStart']                     ={"Target":"Controller","Usage":" GetTimingOutStart MotorNumber","help":" Return timing out start position value of \"MotorNumber\" (0 to 16)."}
        lc_deviceXCTLSTARSCommand['GetTimingOutEnd']                       ={"Target":"Controller","Usage":" GetTimingOutEnd MotorNumber","help":" Return timing out end position value of \"MotorNumber\" (0 to 16)."}
        lc_deviceXCTLSTARSCommand['GetTimingOutInterval']                  ={"Target":"Controller","Usage":" GetTimingOutInterval MotorNumber","help":" Return timing out interval value of \"MotorNumber\" (0 to 16)."}
        lc_deviceXCTLSTARSCommand['GetTimingOutReady']                     ={"Target":"Controller","Usage":" GetTimingOutReady MotorNumber","help":" Return timing out ready value of \"MotorNumber\" (0 to 16)."}
        lc_deviceXCTLSTARSCommand['SetHPMode']                             ={"Target":"Controller","Usage":" SetHPMode MotorNumber 0XYZ","help":" Set home position scan mode and status 4 digits value of \"MotorNumber\" (0 to 16) into \"0XYZ\" as     0: preserved, always 0     X: found status, 0/not found 1/found     Y: found direction, 0/cw 1/ccw     Z: auto start direction, 0/cw 1/ccw"}
        lc_deviceXCTLSTARSCommand['GetHPMode']                             ={"Target":"Controller","Usage":" GetHPMode MotorNumber","help":" Return home position scan mode and status 4 digits value of \"MotorNumber\" (0 to 16)."}
        lc_deviceXCTLSTARSCommand['SetHomePosition']                       ={"Target":"Controller","Usage":" SetHomePosition MotorNumber Value","help":" Write home position pulse of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceXCTLSTARSCommand['GetHomePosition']                       ={"Target":"Controller","Usage":" GetHomePosition MotorNumber","help":" Return home position pulse value of \"MotorNumber\" (0 to 16)."}
        lc_deviceXCTLSTARSCommand['SetHPOffset']                           ={"Target":"Controller","Usage":" SetHPOffset MotorNumber Value","help":" Set home position offset value used in rescanning of \"MotorNumber\" (0 to 16) into \"Value\"."}
        lc_deviceXCTLSTARSCommand['GetHPOffset']                           ={"Target":"Controller","Usage":" GetHPOffset MotorNumber","help":" Return home position offset value used in rescanning of \"MotorNumber\" (0 to 16)."}
        lc_deviceXCTLSTARSCommand['SetMotorSetup']                         ={"Target":"Controller","Usage":" SetMotorSetup MotorNumber ABCD","help":" Set motor basic properties 4 digits value of \"MotorNumber\" (0 to 16) into \"ABCD\" as    A: 1/drive enable 0/drive disable     B: 1/hold on 0/hold off     C: 0/const 1/trapezoidal 2/S character     D: 0/Pulse-Pulse 1/Pulse-Direction"}
        lc_deviceXCTLSTARSCommand['GetMotorSetup']                         ={"Target":"Controller","Usage":" GetMotorSetup MotorNumber","help":" Return motor basic properties 4 digits value of \"MotorNumber\" (0 to 16)."}
        lc_deviceXCTLSTARSCommand['SetStopMode']                           ={"Target":"Controller","Usage":" SetStopMode MotorNumber AB","help":" Set stop mode 2 digits value of \"MotorNumber\" (0 to 16) into \"AB\" as     A: how to stop for cw/ccw limit switch, 0/LS slow stop 1/LS fast stop     B: how to stop for panel stop button , 0/PB slow stop 1/PB fast stop"}
        lc_deviceXCTLSTARSCommand['GetStopMode']                           ={"Target":"Controller","Usage":" GetStopMode MotorNumber","help":" Get stop mode 2 digits value of \"MotorNumber\" (0 to 16)."}
        lc_deviceXCTLSTARSCommand['ReScanHome']                            ={"Target":"Controller","Usage":" ReScanHome MotorNumber","help":" Move \"MotorNumber\" (0 to 16) near to the home position previously found fastly, then start finding home position."}
        lc_deviceXCTLSTARSCommand['GetChannelStatus']                      ={"Target":"Controller","Usage":" GetChannelStatus","help":" Return information of selected channels.    Return Data Format: [R|L]abcd/PNNS/VVVV/HHJJKKLL/+-uu.../+-vv.../+-ww.../+-xx...    \"R\" or \"L\"  Remote or Local    \"abcd\"      Selected MotorNumbers(0 - F) of Channel A,B,C,D    \"PNNS\"      Drive status (P:cw, N:ccw, S:Stop) of Channel A,B,C,D    \"VVVV\"      Ls status and Hold off Status (bit0:cw ls, bit1:ccw ls, bit2:hp ls, bit3:hold off(1/hold off 0/hold on) of Channel A,B,C,D    \"HHJJKKLL\"  Motor current status        bit 0: BUSY, 1: Pulse output running, 2: Accelerating, 3: Decelerating            4: Error, 5: Stopped by LS, 6: Stopped slowly 7: Stopped fastly    \"+-uu...\"   current of Channel A    \"+-vv...\"   current of Channel B    \"+-ww...\"   current of Channel C    \"+-xx...\"   current of Channel D"}
        lc_deviceXCTLSTARSCommand['ScanHome']                              ={"Target":"Controller","Usage":" ScanHome MotorNumber","help":" Move \"MotorNumber\" (0 to 16) for finding home position."}
        lc_deviceXCTLSTARSCommand['SetAutoChangeSpeed']                    ={"Target":"Controller","Usage":" SetAutoChangeSpeed MotorNumber DataNumber ConditionCode ConditionValue FunctionCode FunctionValue","help":" Set parameters of Auto-Change-Speed function of \"MotorNumber\" (0 to 16), DataNumber    0 to 127.        <ConditionCode : ConditionValue : Set condition to execute function>  ;   <\"ADD\" : within +-2147483647 : relative address from start point.>, <\"TIM\" : 0 to 65535 : relative time(ms) from previous point.>, <\"ACC\" : 1 to 5000000 : speed data(pps) while acceleration.>, <\"DEC\" : 1 to 5000000 : speed data(pps) while deceleration.>, <\"END\" : N/A,ignored : End of record.>        <FunctionCode : FunctionValue : Action speed.>  ; <\"SPD\" : 1 to 5000000 : speed in pps>, <\"RTE\" : 0 to 115 : rate code number>, <\"SLW\" : N/A,ignored : slow stop>, <\"FST\" : N/A,ignored : fast stop>, <\"NOP\" : N/A,ignored : no operation>, <N/A,ignored : N/A,ignored :  when \"ConditionCode\" equals \"END\">"}
        lc_deviceXCTLSTARSCommand['SetAutoChangeSpeedReady']               ={"Target":"Controller","Usage":" SetAutoChangeSpeedReady MotorNumber 1|0","help":" Set Auto-Change-Speed function ready (set=1, clear=0) of \"MotorNumber\" (0 to 16)."}
        lc_deviceXCTLSTARSCommand['GetAutoChangeSpeed']                    ={"Target":"Controller","Usage":" GetAutoChangeSpeed MotorNumber DataNumber","help":" Get parameters of Auto-Change-Speed function of \"DataNumber\" of \"MotorNumber\" (0 to 16).\n\n        DataNumber    0 to 127.\n\n    Return Value:\n        ConditionCode ConditionValue     Set condition to execute function.\n        ----------------------------------------------------------------------------\n            \"ADD\"   within +-2147483647  relative address from start point.\n            \"TIM\"      0 to 65535        relative time(ms) from previous point.\n            \"ACC\"     1 to 5000000       speed data(pps) while acceleration.\n            \"DEC\"     1 to 5000000       speed data(pps) while deceleration.\n            \"END\"      N/A,ignored       End of record.\n\n        FunctionCode FunctionValue       Action speed.\n        -----------------------------------------------------------------------\n            \"SPD\"     1 to 5000000       speed in pps.\n            \"RTE\"      0 to 115          rate code number.\n            \"SLW\"      N/A,ignored       slow stop.\n            \"FST\"      N/A,ignored       fast stop.\n            \"NOP\"      N/A,ignored       no operation.\n         N/A,ignored   N/A,ignored       when \"ConditionCode\" equals \"END\"."}
        lc_deviceXCTLSTARSCommand['GetAutoChangeSpeedReady']               ={"Target":"Controller","Usage":" GetAutoChangeSpeedReady MotorNumber","help":" Get Auto-Change-Speed function ready (set=1, clear=0) of \"MotorNumber\" (0 to 16)."}
###############################################
#     << PM16CX additional Motor Command >>   #
#---------------------------------------------#
        lc_deviceXMOTSTARSCommand['SpeedLow']                              ={"Target":"Motor","Usage":" SpeedLow","help":" Set speed to \"Low\"."}
        lc_deviceXMOTSTARSCommand['SpeedMiddle']                           ={"Target":"Motor","Usage":" SpeedMiddle","help":" Set speed to \"Middle\"."}
        lc_deviceXMOTSTARSCommand['SpeedHigh']                             ={"Target":"Motor","Usage":" SpeedHigh","help":" Set speed to \"High\"."}
        lc_deviceXMOTSTARSCommand['GetSpeedSelected']                      ={"Target":"Motor","Usage":" GetSpeedSelected","help":" Return selected speed (\"H\" (high), \"M\" (middle), \"L\" (low))."}
        lc_deviceXMOTSTARSCommand['SetSpeedCurrent']                       ={"Target":"Motor","Usage":" SetSpeedCurrent SpeedValue","help":" Change speed to \"SpeedValue\" only while motor running."}
        lc_deviceXMOTSTARSCommand['SetTimingOutMode']                      ={"Target":"Motor","Usage":" SetTimingOutMode Value","help":" Set timing out mode value into \"Value\". Value 0\":\" disable, 1: TTL gate , 2: TTL interval 200ns 3: TTL interval 10us 4: TTL interval 100us, 5: TTL interval 1ms"}
        lc_deviceXMOTSTARSCommand['SetTimingOutStart']                     ={"Target":"Motor","Usage":" SetTimingOutStart Value","help":" Set timing out start position value into \"Value\"."}
        lc_deviceXMOTSTARSCommand['SetTimingOutEnd']                       ={"Target":"Motor","Usage":" SetTimingOutEnd Value","help":" Set timing out end position value into \"Value\"."}
        lc_deviceXMOTSTARSCommand['SetTimingOutInterval']                  ={"Target":"Motor","Usage":" SetTimingOutInterval Value","help":" Set timing out interval value into \"Value\"."}
        lc_deviceXMOTSTARSCommand['SetTimingOutReady']                     ={"Target":"Motor","Usage":" SetTimingOutReady 1|0","help":" Set timing out ready (set=1, clear=0)."}
        lc_deviceXMOTSTARSCommand['GetTimingOutMode']                      ={"Target":"Motor","Usage":" GetTimingOutMode","help":" Return timing out mode value."}
        lc_deviceXMOTSTARSCommand['GetTimingOutStart']                     ={"Target":"Motor","Usage":" GetTimingOutStart","help":" Return timing out start position value."}
        lc_deviceXMOTSTARSCommand['GetTimingOutEnd']                       ={"Target":"Motor","Usage":" GetTimingOutEnd","help":" Return timing out end position value."}
        lc_deviceXMOTSTARSCommand['GetTimingOutInterval']                  ={"Target":"Motor","Usage":" GetTimingOutInterval","help":" Return timing out interval value."}
        lc_deviceXMOTSTARSCommand['GetTimingOutReady']                     ={"Target":"Motor","Usage":" GetTimingOutReady","help":" Return timing out ready value."}
        lc_deviceXMOTSTARSCommand['SetHPMode']                             ={"Target":"Motor","Usage":" SetHPMode 0XYZ","help":" Set home position scan mode and status 4 digits value into \"0XYZ\" as\n     0: preserved, always 0\n     X: found status, 0/not found 1/found\n     Y: found direction, 0/cw 1/ccw\n     Z: auto start direction, 0/cw 1/ccw"}
        lc_deviceXMOTSTARSCommand['GetHPMode']                             ={"Target":"Motor","Usage":" GetHPMode","help":" Return home position scan mode and status 4 digits value."}
        lc_deviceXMOTSTARSCommand['SetHomePosition']                       ={"Target":"Motor","Usage":" SetHomePosition Value","help":" Write home position pulse into \"Value\"."}
        lc_deviceXMOTSTARSCommand['GetHomePosition']                       ={"Target":"Motor","Usage":" GetHomePosition","help":" Return home position pulse value."}
        lc_deviceXMOTSTARSCommand['SetHPOffset']                           ={"Target":"Motor","Usage":" SetHPOffset Value","help":" Set home position offset value used in rescanning into \"Value\"."}
        lc_deviceXMOTSTARSCommand['GetHPOffset']                           ={"Target":"Motor","Usage":" GetHPOffset","help":" Return home position offset value used in rescanning."}
        lc_deviceXMOTSTARSCommand['SetMotorSetup']                         ={"Target":"Motor","Usage":" SetMotorSetup ABCD","help":" Set motor basic properties 4 digits value into \"ABCD\" as\n     A: 1/drive enable 0/drive disable\n     B: 1/hold on 0/hold off\n     C: 0/const 1/trapezoidal 2/S character\n     D: 0/Pulse-Pulse 1/Pulse-Direction"}
        lc_deviceXMOTSTARSCommand['GetMotorSetup']                         ={"Target":"Motor","Usage":" GetMotorSetup","help":" Return motor basic properties 4 digits value."}
        lc_deviceXMOTSTARSCommand['SetStopMode']                           ={"Target":"Motor","Usage":" SetStopMode AB","help":" Set stop mode 2 digits value into \"AB\" as\n     A: how to stop for cw/ccw limit switch, 0/LS slow stop 1/LS fast stop\n     B: how to stop for panel stop button , 0/PB slow stop 1/PB fast stop"}
        lc_deviceXMOTSTARSCommand['GetStopMode']                           ={"Target":"Motor","Usage":" GetStopMode","help":" Get stop mode 2 digits value."}
        lc_deviceXMOTSTARSCommand['ReScanHome']                            ={"Target":"Motor","Usage":" ReScanHome","help":" Move near to the home position previously found fastly, then start finding home position."}
        lc_deviceXMOTSTARSCommand['ScanHome']                              ={"Target":"Motor","Usage":" ScanHome","help":" Move for finding home position."}
        lc_deviceXMOTSTARSCommand['SetAutoChangeSpeed']                    ={"Target":"Motor","Usage":" SetAutoChangeSpeed DataNumber ConditionCode ConditionValue FunctionCode FunctionValue","help":" Set parameters of Auto-Change-Speed function.\n\n        DataNumber    0 to 127.\n\n        ConditionCode ConditionValue     Set condition to execute function.\n        ----------------------------------------------------------------------------\n            \"ADD\"   within +-2147483647  relative address from start point.\n            \"TIM\"      0 to 65535        relative time(ms) from previous point.\n            \"ACC\"     1 to 5000000       speed data(pps) while acceleration.\n            \"DEC\"     1 to 5000000       speed data(pps) while deceleration.\n            \"END\"      N/A,ignored       End of record.\n\n        FunctionCode FunctionValue       Action speed.\n        -----------------------------------------------------------------------\n            \"SPD\"     1 to 5000000       speed in pps.\n            \"RTE\"      0 to 115        rate code number.\n            \"SLW\"      N/A,ignored       slow stop.\n         \"FST\"      N/A,ignored       fast stop.\n            \"NOP\"      N/A,ignored       no operation.\n         N/A,ignored   N/A,ignored       when \"ConditionCode\" equals \"END\"."}
        lc_deviceXMOTSTARSCommand['SetAutoChangeSpeedReady']               ={"Target":"Motor","Usage":" SetAutoChangeSpeedReady 1|0","help":" Set Auto-Change-Speed function ready (set=1, clear=0)."}
        lc_deviceXMOTSTARSCommand['GetAutoChangeSpeed']                    ={"Target":"Motor","Usage":" GetAutoChangeSpeed DataNumber","help":" Get parameters of Auto-Change-Speed function of \"DataNumber\".\"\\n \\n        DataNumber    0 to 127.\n\n    Return Value:\n        ConditionCode ConditionValue     Set condition to execute function.\n        ----------------------------------------------------------------------------\n            \"ADD\"   within +-2147483647  relative address from start point.\n            \"TIM\"      0 to 65535        relative time(ms) from previous point.\n            \"ACC\"     1 to 5000000       speed data(pps) while acceleration.\n            \"DEC\"     1 to 5000000       speed data(pps) while deceleration.\n            \"END\"      N/A,ignored       End of record.\n\n        FunctionCode FunctionValue       Action speed.\n        -----------------------------------------------------------------------\n            \"SPD\"     1 to 5000000       speed in pps.\n            \"RTE\"      0 to 115          rate code number.\n            \"SLW\"      N/A,ignored       slow stop.\n            \"FST\"      N/A,ignored       fast stop.\n            \"NOP\"      N/A,ignored       no operation.\n         N/A,ignored   N/A,ignored       when \"ConditionCode\" equals \"END\"."}
        lc_deviceXMOTSTARSCommand['GetAutoChangeSpeedReady']               ={"Target":"Motor","Usage":" GetAutoChangeSpeedReady","help":" Get Auto-Change-Speed function ready (set=1, clear=0)."}






        # Speed rate  ; @::speed
        lc_MotorSpeed = [       5,   10,   25,   50,   75,  100,  150,  200,  250,  300,  350,  400,  450,  500,  550,  600,  650,  700,  750,  800,  900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800,
                             1900, 2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000, 3100, 3200, 3300, 3400, 3500, 3600, 3700, 3800, 3900, 4000, 4100, 4200, 4300, 4400, 4500, 4600, 4700, 4800,
                             4900, 5000, 5100, 5200, 5300, 5400, 5500, 5600, 5700, 5800, 5900, 6000, 6100, 6200, 6300, 6400, 6500, 6600, 6700, 6800, 6900, 7000, 7100, 7200, 7300, 7400, 7500, 7600, 7700, 7800,
                             7900, 8000, 8200, 8400, 8600, 8800, 9000, 9200, 9400, 9600, 9800,10000,10200,10400,10600,10800,11010,11210,11410,11600,11800,11990,12200,12400,12600,12790,12990,13200,13400,13620,
                            13810,14000,14200,14400,14620,14830,15010,15200,15390,15580,15770,15970,16180,16400,16610,16830,17060,17240,17420,17600,17800,17990,18180,18380,18660,18940,19230,19530,19840,20160,
                            20500,20830,21190,12550,21930,22320,22730,23150,23590,24040,24510,25000,25510,26040,26600,27170,27620,28090,28570,29070,29590,30120,30680,31250,31850,32470,33110,33780,34480,35210,
                            35970,36500,37040,37600,38170,38760,39370,40000]
        #
        # Acceleration rate  ; @::rate
        lc_MotorSpeedRate = [1000,800,600,500,400,300,200,150,125,100,75,50,30,20,15,10,7.5,5,3]

        # Acceleration rate  ; @::rateX
        lc_AccelarationRate = [
            1000,    910,    820,    750,    680,    620,    560,    510,    470,    430,    390,    360,    330,    300,    270,    240,    220,    200,    180,    160,    150,    130,    120,    110,
             100,     91,     82,     75,     68,     62,     56,     51,     47,     43,     39,     36,     33,     30,     27,     24,     22,     20,     18,     16,     15,     13,     12,     11,
              10,      9.1,    8.2,    7.5,    6.8,    6.2,    5.6,    5.1,    4.7,    4.3,    3.9,    3.6,    3.3,    3.0,    2.7,    2.4,    2.2,    2.0,    1.8,    1.6,    1.5,    1.3,    1.2,    1.1,
               1.0,    0.91,   0.82,   0.75,   0.68,   0.62,   0.56,   0.51,   0.47,   0.43,   0.39,   0.36,   0.33,   0.30,   0.27,   0.24,   0.22,   0.20,   0.18,   0.16,   0.15,   0.13,   0.12,   0.11,
               0.10,   0.091,  0.082,  0.075,  0.068,  0.062,  0.056,  0.051,  0.047,  0.043,  0.039,  0.036,  0.033,  0.030,  0.027,  0.024,  0.022,  0.020,  0.018,  0.016 ]

        ##################################################################
        #                          table end                             #
##########################################################################
        self._deviceComSTARSCommand = lc_deviceComSTARSCommand
        self._deviceCTLSTARSCommand = lc_deviceCTLSTARSCommand
        self._deviceMOTSTARSCommand = lc_deviceMOTSTARSCommand
        self._deviceXCTLSTARSCommand = lc_deviceXCTLSTARSCommand
        self._deviceXMOTSTARSCommand = lc_deviceXMOTSTARSCommand

        self._MotorSpeed = lc_MotorSpeed
        self._MotorSpeedRate = lc_MotorSpeedRate
        self._AccelarationRate = lc_AccelarationRate 
        self._deviceCommandLastExecutedTime = time.time()
        self._inthandler = inthandler

    ##################################################################
    # Internal Functions
    ##################################################################
    def _set_commandlastwaittime(self,t):
        self._deviceCommandLastWaitTime=t;

#----------------------------------------------------------------
# Program m2701drv.py
#----------------------------------------------------------------
if __name__ == "__main__":
    ##################################################################
    # Import modules
    ##################################################################
    import sys
    import os
    from singlestars import StarsInterface
    from stars import StarsMessage
    from pystarsutil import pystarsutilconfig, pystarsutilargparser
    ##################################################################
    # Define program parameters
    ##################################################################
    # Initialize: Global parameters
    gb_ScriptName = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    #ScriptPath = os.path.dirname(os.path.abspath(sys.argv[0]))
    gb_Debug = False
#    gb_NumberOfChannels = 1  # Set default number of channels.
    gb_MotorNameList = []           # Assumed to be used in the motor name discribed comfig.cfg
#    gb_ChannelNameSeqList = []
#    gb_ChannelNameList = {}
    gb_StarsInstance = None
    gb_DeviceInstance = None
    gb_RegInstance = None         # Cache instance  for 7700, 20220311
    gb_StarsLocalBusyFlg   = 0
    gb_StarsLastSendBusyFlg = -1
    gb_DelimiterOfGetValues = ','
    gb_DelimiterApplyNodeList = {}
#
    gb_userconfigfile = True                # 20220831
# for display informations to cliant windows
    gb_devicename = ''
    gb_cliant = ''
# Remote/Local ; 0:Local, 1:Remote
    gb_Flg_remote = '0'
# IsBusy
    gb_Is_busyflg_A = 'nE'
    gb_Is_busyflg_B = 'nE'
    gb_Is_busyflg_C = 'nE'
    gb_Is_busyflg_D = 'nE'
    gb_Is_eventsE_A = 'ON'
    gb_Is_eventsE_B = 'ON'
    gb_Is_eventsE_C = 'ON'
    gb_Is_eventsE_D = 'ON'

    gb_MotorBusy = ['0','0','0','0','0','0','0','0','0','0','0','0','0','0','0','0']
    _Flg_IsBusy = [gb_Is_busyflg_A,gb_Is_busyflg_B,gb_Is_busyflg_C,gb_Is_busyflg_D]
# Information for Control
    gb_CancelBacklash = ['','','','','','','','','','','','','','','','']
# SendRawCommand
    gb_SRawC = False
# SupportDeviceFlg
    gb_pm16cx = 'off'
    supportdevice = 'no'
# constant for time control
    WAIT_MEMWRITE = 40/1000
    WAIT_HOLD_ON = 100/1000
    WAIT_HOLD_OFF = 500/1000
    WAIT_SELECT = 40/1000
    INTERVAL_STOP = 2000/1000
    INTERVAL_RUN = 100/1000
#    INTERVAL_RUN = 100/10
    REFRESH_RUN = 500/1000
    WAIT_BUB = 100/1000
# time interval control
    gb_Elaps = 0
    gb_Interval_Time = INTERVAL_RUN
    gb_Buf_Interval = 0
# 2drive extratime
    gb_2Dext = '0'


# Define: Appliction default parameters
    starsServerHost = 'localhost'
    starsNodeName   = 'tdkzplus'
    starsServerPort = 6057
    deviceHost = '172.16.0.53' #169.254.9.35
    devicePort = 7777  #8003
    motorname = 'th'
    motorname_l = []
#    modeofgetsetvalue = 'CC'


# need to access config.cfg     20220829


#################################################################################
#           Function definition       >>>>>>>>>>>>>>>>>>>                       #
#################################################################################

    ##################################################################
    # Define local functions: print
    ##################################################################
    # Define: print function
    #from logging import NOTSET,DEBUG,INFO,WARN,WARNING,ERROR,CRITICAL,FATAL
    DEBUG = 10
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
        global gb_pm16cx
        pm16cx = gb_pm16cx
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
        
        if(pm16cx == 'on'):
            dc.intervalX()
        else:
            dc.interval()
#
        dc.setdebug(debugmode)
        st.setdebug(debugmode)
#        
        return

    ## STARS socket handler
    def handler(allmess,sock):
        global gb_ScriptName
        global gb_StarsInstance
#        global gb_ChannelNameList
#        global gb_ChannelNameSeqList
        global gb_DeviceInstance
        global gb_Debug
# for treat to the IsBusy 20220316
        global Is_busyflg
        global Is_eventsE
# <- 20220316
#
        global gb_RegInstance       #20220415, to add GenerateConfigFile
        global gb_userconfigfile    #20220415, to add GenerateConfigFile 
#
        global gb_MotorNameList
        global gb_pm16cx
#
        global gb_Flg_remote
#
        global gb_devicename
        global gb_cliant
#
        global gb_CancelBacklash
#
        global gb_Is_busyflg_A
        global gb_Is_busyflg_B
        global gb_Is_busyflg_C
        global gb_Is_busyflg_D
        global gb_Is_eventsE_A
        global gb_Is_eventsE_B
        global gb_Is_eventsE_C
        global gb_Is_eventsE_D
        global gb_MotorBusy
#
        global gb_Elaps
#
        dc = gb_DeviceInstance
        st = gb_StarsInstance
#
        motorlist = gb_MotorNameList
#        cancelB = gb_CancelBacklash
        pm16cx = gb_pm16cx
#
#        Flg_Remote = gb_Flg_remote
#
        Flg_Busy_A = gb_Is_busyflg_A
        Flg_Busy_B = gb_Is_busyflg_B
        Flg_Busy_C = gb_Is_busyflg_C
        Flg_Busy_D = gb_Is_busyflg_D
        Flg_IsBusy = [Flg_Busy_A,Flg_Busy_B,Flg_Busy_C,Flg_Busy_D]
        Flg_Event_A = gb_Is_eventsE_A
        Flg_Event_B = gb_Is_eventsE_B
        Flg_Event_C = gb_Is_eventsE_C
        Flg_Event_D = gb_Is_eventsE_D
        Flg_IsEvent = [Flg_Event_A,Flg_Event_B,Flg_Event_C,Flg_Event_D]

        Flg_MotBusy = gb_MotorBusy

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
#
#        print('\n' + ' <<---  command parameter  --->>>>> ' + str(message) + '\n')     # for making sure 20220905
#        print('\n' + ' <<---   nodeto   --->>>>> ' + str(allmess.nodeto) + '\n')     # for making sure 20220906
#        print('\n' + ' <<---  nodefrom  --->>>>> ' + str(allmess.nodefrom) + '\n')     # for making sure 20220906

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


        if(allmess.nodeto.startswith(st.nodename+'.')):
#             channelname=allmess.nodeto.replace(st.nodename+'.','')
#             _outputlog(DEBUG, "Debug: Channel coming" + channelname)

######################################################################
##   Motor handler process  ; currentmotor = _currentmotor
######################################################################
            _category = 'Motor'
            _currentMNo = ''
            _currentMNox = ''
            _cmck = 'bad'
            _currentmotor = allmess.nodeto.split('.')[1]
            if( _currentmotor not in motorlist):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + 'Er: The name of a motor that does not exist. '
                _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
                rt=st.send(destsendstr)
                return
            else:
                for v in range(0,16):
                    if(_currentmotor == motorlist[v]):
                        _currentMNo = str(v)
                        _cmck = v
                        break
                if (_cmck == 'bad'):
                    destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + 'Er: The motornumber does not exist. '
                    _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
                    rt=st.send(destsendstr)
                    return
            _currentMNox = format(_cmck,'X')
#
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
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' '+rt
            elif(message == 'getversionno'):
                rt = __version__
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Ver.'+rt
            elif(message == 'hello'):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '  My name is ' + str(_currentmotor) + '. Nice to meet you.'
            elif(message == 'help'):
                clist1=sorted(dc.get_commandlist(pm16cx,_category))
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + ' '.join(clist1)
            elif(command == 'help' and len(parameters) == 1):
                rt=parameters[0]
                _rt = dc.is_commanddefined(pm16cx,_category,parameters[0])
                if(_rt == False):
                    rt='Er: Command not found'
                else:
                    rt=dc.get_commandhelp(_rt, parameters[0])
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(rt)   # str() 20220913
            elif( message == 'GetAccRateList'):
                _rt = dc.get_AccRate(pm16cx)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + str(_rt)
            elif( message == 'GetSpeedList'):
                _rt = dc.get_motorspeed_n4x(pm16cx)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + str(_rt)

#################
            elif((pm16cx == 'on') and (message == 'GetAccRateCode')):
                _mnox = _currentMNox
                _rt = dc.MotorX_GetAccRateCode(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + str(_rt)
            elif(message == 'GetAccRateCode'):
                _mnox = _currentMNox
                _rt = dc.Motor_GetAccRateCode(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + str(_rt)
            elif((pm16cx == 'on') and (message == 'GetAccRate')):
                _mnox = _currentMNox
                _rt = dc.MotorX_GetAccRate(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + str(_rt)

            elif( message == 'GetAccRate'):
                _mnox = _currentMNox
                _rt = dc.Motor_GetAccRate(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + str(_rt)

            elif((pm16cx == 'on' ) and (( command == 'GetAutoChangeSpeed') and (len(parameters)== 1))):
                _mnox = _currentMNox
                _ln = parameters[0]
                _rt = dc.Motor_GetAutoChangeSpeed(_mnox,_ln)

                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif((pm16cx == 'on' ) and ( message == 'GetAutoChangeSpeedReady')):
                _mnox = _currentMNox
                _rt = dc.Motor_GetAutoChangeSpeedReady(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif( message == 'GetCancelBacklash'):
                _rt = 'Er:'
                _mno = _currentMNo
                _rt =  dc.Motor_GetCancelBacklash(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif( message == 'GetDigitalCcwLs'):
                _mno = _currentMNo
                _rt = dc.Motor_GetDigitalCcwLs(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + str(_rt)

            elif( message == 'GetDigitalCwLs'):
                _mno = _currentMNo
                _rt = dc.Motor_GetDigitalCwLs(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + str(_rt)

            elif( message == 'GetHighSpeed'):
                _mnox = _currentMNox
                _spf = 'H'
                _rt = dc.Motor_GetHMLspeed(_mnox,_spf)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif(message == 'GetHold'):
                _mnox = _currentMNox
                _rt = dc.Motor_GetHold(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt


            elif((pm16cx == 'on' ) and ( message == 'GetHomePosition')):
                _mnox = _currentMNox
                _rt = dc.MotorX_GetHPValue(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and (message == 'GetHPMode')):
                _mnox = _currentMNox
                _rt = dc.MotorX_GetHPsettings(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and (message == 'GetHPOffset')):
                _mnox = _currentMNox
                _rt = dc.MotorX_GetHPOffset(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'GetJogPulse'):
                _mnox = _currentMNox
                _rt = dc.Motor_GetJogPulse(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'GetLimits'):
                _mno = _currentMNo
                _rt = dc.Motor_GetLimits(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'GetLowSpeed'):
                _mnox = _currentMNox
                _spf = 'L'
                _rt = dc.Motor_GetHMLspeed(_mnox,_spf)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'GetMiddleSpeed'):
                _mnox = _currentMNox
                _spf = 'M'
                _rt = dc.Motor_GetHMLspeed(_mnox,_spf)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'GetMotorNumber'):
                _rt = _currentMNo
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ( message == 'GetMotorSetup')):
                _mnox = _currentMNox
                _rt = dc.MotorX_GetMotorSettings(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'GetSelected'):                
                rt = dc.Motor_GetSelected(_currentmotor)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt

            elif((pm16cx == 'on' ) and ( message == 'GetSpeedSelected')):
                _mnox = _currentMNox
                _rt = dc.MotorX_GetSpeedSelect(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ( command == 'GetStopMode')):
                _mnox = _currentMNox
                _rt = dc.MotorX_GetMotorStop(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ( message == 'GetTimingOutEnd')):
                _mnox = _currentMNox
                _sf = 'E'
                _rt = dc.MotorX_gettimingoutsetting(_mnox,_sf)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ( message == 'GetTimingOutInterval')):
                _mnox = _currentMNox
                _sf = 'I'
                _rt = dc.MotorX_gettimingoutsetting(_mnox,_sf)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ( message == 'GetTimingOutMode')):
                _mnox = _currentMNox
                _sf = 'M'
                _rt = dc.MotorX_gettimingoutsetting(_mnox,_sf)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and (message == 'GetTimingOutReady')):
                _mn = _currentmotor
                _mnox = _currentMNox
                _rt = 'Er:'
                _rstm = dc.Motor_GetSelected(_mn)
                if( _rstm=='N' ):
                    _rt = _rt + ' not set to channel.'
                    destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt
                else:
                    _rt = dc.MotorX_GetTimingOutReady(_mnox)
                    destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ( message == 'GetTimingOutStart')):
                _mnox = _currentMNox
                _sf = 'S'
                _rt = dc.MotorX_gettimingoutsetting(_mnox,_sf)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'GetValue'):
                _mno = _currentMNo
                _rt = dc.Motor_GetValue(_mno)
#                _rt = _rtt.lstrip('0')
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'IsBusy'):
                _mnox =_currentMNox
                _rt = dc.Motor_IsBusy(_mnox)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'JogCcw'):
                _mnx = _currentMNox
                _mode ='9'
                _rt = dc.Motor_Scan(_mnx,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'JogCw'):
                _mnx = _currentMNox
                _mode ='8'
                _rt = dc.Motor_Scan(_mnx,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'Preset') and (len(parameters)==1)):
                _mnox = _currentMNox
                _sdata = parameters[0]
                _rt = dc.Motor_Preset(_mnox,_sdata)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ( message == 'ReScanHome')):
                _mnox = _currentMNox
                _mode = 'GT'
                _rt = dc.MotorX_ScanHome(_mnox,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif(	command == 'ScanCcw'):
                _mnox =_currentMNox
                _mode = '0F'
                _rt = dc.Motor_Scan(_mnox,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'ScanCcwConst'):
                _mnox =_currentMNox
                _mode = '0D'
                _rt = dc.Motor_Scan(_mnox,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'ScanCcwHome'):
                _mnox =_currentMNox
                _mode = '1F'
                _rt = dc.Motor_Scan(_mnox,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'ScanCw'):
                _mnox =_currentMNox
                _mode = '0E'
                _rt = dc.Motor_Scan(_mnox,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'ScanCwConst'):
                _mnox =_currentMNox
                _mode = '0C'
                _rt = dc.Motor_Scan(_mnox,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'ScanCwHome'):
                _mnox =_currentMNox
                _mode = '1E'
                _rt = dc.Motor_Scan(_mnox,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ( message == 'ScanHome')):
                _mnox = _currentMNox
                _mode = 'FD'
                _rt = dc.MotorX_ScanHome(_mnox,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on') and (command == 'SetAccRate') and (len(parameters)==1)):
                _mnox =_currentMNox
                _sdata = parameters[0]
                _rt = dc.MotorX_SetAccRate(_mnox,_sdata)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'SetAccRate') and (len(parameters)==1)):
                _mnox =_currentMNox
                _sdata = parameters[0]
                _rt = dc.Motor_SetAccRate(_mnox,_sdata)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ((command == 'SetAutoChangeSpeed') and (len(parameters)<=5) and (len(parameters)>=2))):
                _rt = dc.Motor_SetAutoChangeSpeed(_currentMNox,*parameters)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif((pm16cx == 'on' ) and ((command == 'SetAutoChangeSpeedReady') and (len(parameters)==1))):
                _mno = _currentMNo
                sd = parameters[0]
                _rt = dc.MotorX_SetAutoChangeSpeedReady(_mno,sd) 
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif((command == 'SetCancelBacklash') and (len(parameters)==1)):
                _mno = _currentMNo
                _sd = parameters[0]
                _rt = dc.Motor_SetCancelBacklash(_mno,_sd)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif( (command == 'SetDigitalCcwLs') and (len(parameters)==1)):
                _mnox = _currentMNox
                _lsd = parameters[0]
                _rt = 'Er:'
                try:
                    _ckdti = int(_lsd)
                except ValueError:
                    _rt = _rt + ' Bad parameter'
                if('Bad' not in _rt):
                    _rt = dc.Motor_SetDigitalCcwLs(_mnox,_ckdti)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif( (command == 'SetDigitalCwLs') and (len(parameters) == 1)):
                _mnox = _currentMNox
                _lsd = parameters[0]
                _rt = 'Er:'
                try:
                    _ckdti = int(_lsd)
                except ValueError:
                    _rt = _rt + ' Bad parameter'
                if('Bad' not in _rt):
                    _rt = dc.Motor_SetDigitalCwLs(_mnox,_ckdti)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif((command == 'SetHighSpeed') and (len(parameters)==1)):
                _mnox = _currentMNox
                _sdata = parameters[0]
                _spf = '9'
                _rt = dc.pm16c_setspeedcommon(_mnox,_sdata,_spf)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( (command == 'SetHold') and (len(parameters)==1)):
                _mnox = _currentMNox
                _hld = parameters[0]
                _rt = dc.Motor_SetHold(_mnox,_hld)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif((pm16cx == 'on' ) and ((command == 'SetHomePosition') and (len(parameters)==1))):
                _mnox = _currentMNox
                _sdt = parameters[0]
                _rt = dc.MotorX_HPPreset(_mnox,_sdt)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ((command == 'SetHPMode') and (len(parameters)==1))):
                _mnox = _currentMNox
                _sd = parameters[0]
                _rt = dc.MotorX_SetHPsettings(_mnox,_sd)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ((command == 'SetHPOffset') and (len(parameters)==1))):
                _mnox = _currentMNox
                _sdata = parameters[0]
                _rt = dc.MotorX_SetHPOffset(_mnox,_sdata)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( (command == 'SetJogPulse') and (len(parameters)==1)):
                _mnox = _currentMNox
                _sdata = parameters[0]
                _rt = dc.Motor_SetJogPulse(_mnox,_sdata)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'SetLimits') and (len(parameters)==1)):
                _mnox = _currentMNox
                _sdata = parameters[0]
                _rt = dc.Motor_SetLimits(_mnox,_sdata)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'SetLowSpeed') and (len(parameters)==1)):
                _mnox = _currentMNox
                _sdata = parameters[0]
                _spf = 'B'
                _rt = dc.pm16c_setspeedcommon(_mnox,_sdata,_spf)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'SetMiddleSpeed') and (len(parameters)==1)):
                _mnox = _currentMNox
                _sdata = parameters[0]
                _spf = 'A'
                _rt = dc.pm16c_setspeedcommon(_mnox,_sdata,_spf)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ((command == 'SetMotorSetup') and (len(parameters)==1))):
                _mnox = _currentMNox
                _sdt = parameters[0]
                _rt = dc.MotorX_SetMotorSettings(_mnox,_sdt)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ((command == 'SetSpeedCurrent') and (len(parameters)==1))):
                _mnox = _currentMNox
                _sdata = parameters[0]
                _rt = dc.MotorX_ChangeSpeed(_mnox,_sdata)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ((command == 'SetStopMode') and (len(parameters)==1)) ):
                _mnox = _currentMNox
                _sdt = parameters[0]
                _rt = dc.MotorX_SetMotorStop(_mnox,_sdt)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ((command == 'SetTimingOutEnd') and (len(parameters)==1))):
                _mnox = _currentMNox
                _sf = 'E'
                _setd = parameters[0]
                _rt = dc.MotorX_settimingoutsetting(_mnox,_sf,_setd)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ( command == 'SetTimingOutInterval')):
                _mnox = _currentMNox
                _sf = 'I'
                _setd = parameters[0]
                _rt = dc.MotorX_settimingoutsetting(_mnox,_sf,_setd)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ( command == 'SetTimingOutMode')):
                _mnox = _currentMNox
                _sf = 'M'
                _setd = parameters[0]
                _rt = dc.MotorX_settimingoutsetting(_mnox,_sf,_setd)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and ( command == 'SetTimingOutReady') and (len(parameters)==1)):
                _mn = _currentmotor
                _mnox = _currentMNox
                _sf = parameters[0]
                _rt = 'Er:'
                rt = 'Ok:'
                _rsts = dc.rolMbusy(_mnox)
                if('Er:' in _rsts):
                    rt = _rsts
                _rstm = dc.Motor_GetSelected(_mn)
                if( _rstm=='N' ):
                    rt = _rt + ' not to set channel.'
                else:
                    _rsts = dc.MotorX_SetTimingOutReady(_mnox,_sf)
                    if('Er:' in _rsts):
                        rt = _rsts
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + rt

            elif((pm16cx == 'on' ) and ( command == 'SetTimingOutStart')):
                _mnox = _currentMNox
                _sf = 'S'
                _setd = parameters[0]
                _rt = dc.MotorX_settimingoutsetting(_mnox,_sf,_setd)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'SetValue') and (len(parameters)==1)):
                _mno = _currentMNo
                _sdata = parameters[0]
                _mode = 'ABS'
                _rt = dc.Motor_SetValue(_mno,_sdata,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'SetValueREL') and (len(parameters)==1)):
                _mno = _currentMNo
                _sdata = parameters[0]
                _mode = 'REL'
                _rt = dc.Motor_SetValue(_mno,_sdata,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and (message == 'SpeedHigh')):
                _mnox = _currentMNox
                _spd = 'H'
                _rt = dc.MotorX_SetSpeed(_mnox,_spd)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and (message == 'SpeedLow')):
                _mnox = _currentMNox
                _spd = 'L'
                _rt = dc.MotorX_SetSpeed(_mnox,_spd)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((pm16cx == 'on' ) and (message == 'SpeedMiddle')):
                _mnox = _currentMNox
                _spd = 'M'
                _rt = dc.MotorX_SetSpeed(_mnox,_spd)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif(	command == 'Stop'):
                _mne = _currentmotor
                _mode = '0'
                _rt = dc.Motor_Stop(_mne,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif(	command == 'StopEmergency'):
                _mne = _currentmotor
                _mode = '1'
                _rt = dc.Motor_Stop(_mne,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

##################
            elif(message == 'terminate'):
                st.terminateMainloop()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Ok:'
##################                
            else:
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad command or parameters.'
######################################################################
##   Control handler process  
######################################################################
        elif(allmess.nodeto == st.nodename):
            _category = 'Controller'
            if(message.startswith('@')):
                return
            elif(message.startswith('_')):
                return
            elif(message == 'getversion'):
                rt = gb_ScriptName + ' Ver.'+__version__+', '+__date__+', '+__author__
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' '+rt
            elif(message == 'getversionno'):
                rt = __version__
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Ver.'+rt
            elif(message == 'hello'):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Nice to meet you.'
            elif(message == 'help'):
                clist1=sorted(dc.get_commandlist(pm16cx,_category))
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + ' '.join(clist1)
            elif(command == 'help' and len(parameters) == 1):
                rt=parameters[0]
                _rt = dc.is_commanddefined(pm16cx,_category,parameters[0])
                if(_rt == False):
                    rt='Er: Command not found'
                else:
                    rt=dc.get_commandhelp(_rt, parameters[0])
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + rt
            elif( message == 'GetAccRateList'):
                _rt = dc.get_AccRate(pm16cx)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + str(_rt)
            elif(message == 'GetSpeedList'):
                _rt = dc.get_motorspeed_n4x(pm16cx)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + str(_rt)
            elif(message == 'terminate'):
                st.terminateMainloop()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Ok:'
#
            elif(command == 'SendChangedIsBusy' and len(parameters)==1 ):
                rt = 'Er: Bad parameter'
                if(('ON' in str(parameters[0])) or ('OFF' in str(parameters[0]))):
                    Is_eventsE = parameters[0]
                    rt ='OK'
                destsendstr=allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
#
            elif(message == 'IsBusy'):
                _ch = 'ALL'
                _flgb = dc.Ctl_IsBusy(_ch)
                destsendstr=allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _flgb
#
            elif(( pm16cx == 'on' ) and (command == 'DrawArc') and ((len(parameters)==6) or (len(parameters)==7))):
                _dch = None
                _mode = 'AAC'
                _tcx = None
                _tcy = None
                if(len(parameters)==7):
                    _dch = parameters[0]
                    _mnax = parameters[1]
                    _mnay = parameters[2]
                    _tvx = parameters[3]
                    _tvy = parameters[4]
                    _tcx = parameters[5]
                    _tcy = parameters[6]
                else:
                    _dch = None
                    _mnax = parameters[0]
                    _mnay = parameters[1]
                    _tvx = parameters[2]
                    _tvy = parameters[3]
                    _tcx = parameters[4]
                    _tcy = parameters[5]
                _rt = dc.CtlX_2DriveAxis(_dch,_mode,_mnax,_mnay,_tvx,_tvy,_tcx,_tcy)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif(( pm16cx == 'on' ) and (command == 'DrawArcREL') and ((len(parameters)==6) or (len(parameters)==7))):
                _dch = None
                _mode = 'RAC'
                if(len(parameters)==7):
                    _dch = parameters[0]
                    _mnax = parameters[1]
                    _mnay = parameters[2]
                    _tvx = parameters[3]
                    _tvy = parameters[4]
                    _tcx = parameters[5]
                    _tcy = parameters[6]
                else:
                    _dch = None
                    _mnax = parameters[0]
                    _mnay = parameters[1]
                    _tvx = parameters[2]
                    _tvy = parameters[3]
                    _tcx = parameters[4]
                    _tcy = parameters[5]
                _rt = dc.CtlX_2DriveAxis(_dch,_mode,_mnax,_mnay,_tvx,_tvy,_tcx,_tcy)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif(( pm16cx == 'on' ) and (command == 'DrawCircle') and ((len(parameters)==6) or (len(parameters)==7))):
                _dch = None
                _mode = 'ACC'
                if(len(parameters)==7):
                    _dch = parameters[0]
                    _mnax = parameters[1]
                    _mnay = parameters[2]
                    _tvx = parameters[3]
                    _tvy = parameters[4]
                    _tcx = parameters[5]
                    _tcy = parameters[6]
                else:
                    _dch = None
                    _mnax = parameters[0]
                    _mnay = parameters[1]
                    _tvx = parameters[2]
                    _tvy = parameters[3]
                    _tcx = parameters[4]
                    _tcy = parameters[5]
                _rt = dc.CtlX_2DriveAxis(_dch,_mode,_mnax,_mnay,_tvx,_tvy,_tcx,_tcy)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif(( pm16cx == 'on' ) and (command == 'DrawCircleREL') and ((len(parameters)==6) or (len(parameters)==7))):
                _dch = None
                _mode = 'RCC'
                if(len(parameters)==7):
                    _dch = parameters[0]
                    _mnax = parameters[1]
                    _mnay = parameters[2]
                    _tvx = parameters[3]
                    _tvy = parameters[4]
                    _tcx = parameters[5]
                    _tcy = parameters[6]
                else:
                    _dch = None
                    _mnax = parameters[0]
                    _mnay = parameters[1]
                    _tvx = parameters[2]
                    _tvy = parameters[3]
                    _tcx = parameters[4]
                    _tcy = parameters[5]
                _rt = dc.CtlX_2DriveAxis(_dch,_mode,_mnax,_mnay,_tvx,_tvy,_tcx,_tcy)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif(( pm16cx == 'on' ) and (command == 'DrawCircularCcw') and ((len(parameters)==6) or (len(parameters)==7))):
                _dch = None
                _mode = 'ACN'
                if(len(parameters)==7):
                    _dch = parameters[0]
                    _mnax = parameters[1]
                    _mnay = parameters[2]
                    _tvx = parameters[3]
                    _tvy = parameters[4]
                    _tcx = parameters[5]
                    _tcy = parameters[6]
                else:
                    _dch = None
                    _mnax = parameters[0]
                    _mnay = parameters[1]
                    _tvx = parameters[2]
                    _tvy = parameters[3]
                    _tcx = parameters[4]
                    _tcy = parameters[5]
                _rt = dc.CtlX_2DriveAxis(_dch,_mode,_mnax,_mnay,_tvx,_tvy,_tcx,_tcy)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif(( pm16cx == 'on' ) and (command == 'DrawCircularCcwREL') and ((len(parameters)==6) or (len(parameters)==7))):
                _dch = None
                _mode = 'RCN'
                if(len(parameters)==7):
                    _dch = parameters[0]
                    _mnax = parameters[1]
                    _mnay = parameters[2]
                    _tvx = parameters[3]
                    _tvy = parameters[4]
                    _tcx = parameters[5]
                    _tcy = parameters[6]
                else:
                    _dch = None
                    _mnax = parameters[0]
                    _mnay = parameters[1]
                    _tvx = parameters[2]
                    _tvy = parameters[3]
                    _tcx = parameters[4]
                    _tcy = parameters[5]
                _rt = dc.CtlX_2DriveAxis(_dch,_mode,_mnax,_mnay,_tvx,_tvy,_tcx,_tcy)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif(( pm16cx == 'on' ) and (command == 'DrawCircularCw') and ((len(parameters)==6) or (len(parameters)==7))):
                _dch = None
                _mode = 'ACP'
                if(len(parameters)==7):
                    _dch = parameters[0]
                    _mnax = parameters[1]
                    _mnay = parameters[2]
                    _tvx = parameters[3]
                    _tvy = parameters[4]
                    _tcx = parameters[5]
                    _tcy = parameters[6]
                else:
                    _dch = None
                    _mnax = parameters[0]
                    _mnay = parameters[1]
                    _tvx = parameters[2]
                    _tvy = parameters[3]
                    _tcx = parameters[4]
                    _tcy = parameters[5]
                _rt = dc.CtlX_2DriveAxis(_dch,_mode,_mnax,_mnay,_tvx,_tvy,_tcx,_tcy)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif(( pm16cx == 'on' ) and (command == 'DrawCircularCwREL') and ((len(parameters)==6) or (len(parameters)==7))):
                _dch = None
                _mode = 'RCP'
                if(len(parameters)==7):
                    _dch = parameters[0]
                    _mnax = parameters[1]
                    _mnay = parameters[2]
                    _tvx = parameters[3]
                    _tvy = parameters[4]
                    _tcx = parameters[5]
                    _tcy = parameters[6]
                else:
                    _dch = None
                    _mnax = parameters[0]
                    _mnay = parameters[1]
                    _tvx = parameters[2]
                    _tvy = parameters[3]
                    _tcx = parameters[4]
                    _tcy = parameters[5]
                _rt = dc.CtlX_2DriveAxis(_dch,_mode,_mnax,_mnay,_tvx,_tvy,_tcx,_tcy)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif(( pm16cx == 'on' ) and (command == 'DrawLine') and ((len(parameters)==4) or (len(parameters)==5))):
                _dch = None
                _mode = 'ALN'
                _tcx = None
                _tcy = None
                if(len(parameters)==5):
                    _dch = parameters[0]
                    _mnax = parameters[1]
                    _mnay = parameters[2]
                    _tvx = parameters[3]
                    _tvy = parameters[4]
                else:
                    _dch = None
                    _mnax = parameters[0]
                    _mnay = parameters[1]
                    _tvx = parameters[2]
                    _tvy = parameters[3]
                _rt = dc.CtlX_2DriveAxis(_dch,_mode,_mnax,_mnay,_tvx,_tvy,_tcx,_tcy)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif(( pm16cx == 'on' ) and (command == 'DrawLineREL') and ((len(parameters)==4) or (len(parameters)==5))):
                _dch = None
                _mode = 'RLN'
                _tcx = None
                _tcy = None
                if(len(parameters)==5):
                    _dch = parameters[0]
                    _mnax = parameters[1]
                    _mnay = parameters[2]
                    _tvx = parameters[3]
                    _tvy = parameters[4]
                else:
                    _dch = None
                    _mnax = parameters[0]
                    _mnay = parameters[1]
                    _tvx = parameters[2]
                    _tvy = parameters[3]
                _rt = dc.CtlX_2DriveAxis(_dch,_mode,_mnax,_mnay,_tvx,_tvy,_tcx,_tcy)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'flushdata'):
                _rt = dc.pm16c_flushdata()
                _result = _rt.split('.',1)
                _flgtmp = eval(_result[1])
                gb_Is_busyflg_A = _flgtmp[0]
                gb_Is_busyflg_B = _flgtmp[1]
                gb_Is_busyflg_C = _flgtmp[2]
                gb_Is_busyflg_D = _flgtmp[3]
                isbusyflgCtl(_result[0])
                rt = 'Ok:'
                _destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
                st.send(_destsendstr)
                dc.Ctl_GetFunction()
                return(rt)

            elif( message == 'flushdatatome'):
                _rt = dc.pm16c_flushdata()
                _result = _rt.split('.',1)
                _flgtmp = eval(_result[1])
                gb_Is_busyflg_A = _flgtmp[0]
                gb_Is_busyflg_B = _flgtmp[1]
                gb_Is_busyflg_C = _flgtmp[2]
                gb_Is_busyflg_D = _flgtmp[3]
                isbusyflgCtl(_result[0])
                rt = 'Ok:'
                _destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
                st.send(_destsendstr)
                dc.Ctl_GetFunction(fm='on')
                return(rt)

            elif(( pm16cx == 'on' ) and (message == 'GetChannelStatus')):
                _rt = dc.pm16cX_GetSTS()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
            elif( message == 'GetCtlIsBusy'):
                _rt = dc.Ctl_IsBusy()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
            elif( message == 'GetFunction'):
                _rt = dc.Ctl_GetFunction()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
            elif( message == 'GetFunctionStatus'):
                _rt = dc.Ctl_GetFunctionStatus()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
            elif( message == 'GetMotorList'):
                _mlistD =''
                for v in range(16):
                    _mlistD = str(_mlistD) + ', ' +str(v) + ':' + motorlist[v]
                _mlistD = _mlistD.lstrip(',')
                _mlistD = ' ; MotorNumber:MortorName -> [ ' + _mlistD + ' ]'
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + str(_mlistD)

            elif( (command == 'GetMotorName') and (len(parameters)==1) ):
                _num = parameters[0]
                _stat = 'Ok:'
                _rt = ' Please specify the number from 0 to 15.'
                try:
                    _ckdti = int(_num)
                except ValueError:
                    _stat = 'Er:'
                if( _stat == 'Ok:'):
                    if( _ckdti >= 0 and _ckdti <= 15):
                        _rt = motorlist[_ckdti]
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'GetMotorNumber') and (len(parameters)==1)):
                _motorname = parameters[0]
                _mno = ''
                _rt = 'Er:'

                for v in range(0,16):
                    if(_motorname == motorlist[v]):
                        _mno = str(v)
                        _rt = 'InList'
                        break
                if('InList' in _rt):
                    _rt = _mno
                else:
                    _rt =  _rt + ' MotorName = ' + _motorname + ' not in list.'
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt
            elif( message == 'GetRomVersion'):
                _com = 'VER?'
                _rt = dc.device_act(_com)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif((command == 'GetSelected') and (len(parameters)==1)):
                _chs = parameters[0]
                _rt = dc.Ctl_GetSelected(_chs)
                if('Er:' not in _rt):
                    _rtt = int(_rt,16)
                    _rt = ': ' + str(_rtt)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif((command == 'GetStatus') and (len(parameters)==1)):
                _ch = parameters[0]
                _rtst = dc.Ctl_getstatus(_ch)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + str(_rtst)

            elif((command == 'GetValue') and (len(parameters)==1)):
                _ch = parameters[0]
                _rt = dc.Ctl_GetValue(_ch)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif((command == 'IsBusy') and (len(parameters)==1)):
                _ch = parameters[0]
                _rt = dc.Ctl_IsBusy(_ch)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'JogCcw') and (len(parameters)==1)):
                _ch = parameters[0]
                _mode = '9'
                _rt = dc.Ctl_Scan(_ch,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'JogCw') and (len(parameters)==1)):
                _ch = parameters[0]
                _mode = '8'
                _rt = dc.Ctl_Scan(_ch,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif( message == 'Local'):
                _rt = 'Ok:' 
                _rsts = dc.Ctl_SetFunction('0')
                if('Er:' in _rsts):
                    _rt = _rsts
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

#            elif(	command == 'Preset'):
#                rt = ''
#                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + rt

            elif( message == 'Remote'):
                _rt = 'OK:'
                _rsts = dc.Ctl_SetFunction('1')
                if('Er:' in _rsts):
                    _rt = _rsts
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

#            elif(( pm16cx == 'on' ) and (command == 'ReScanHome')):
#                rt = ''
#                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + rt

            elif( (command == 'ScanCcw') and (len(parameters)==1)):
                _ch = parameters[0]
                _mode = '0F'
                _rt = dc.Ctl_Scan(_ch,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'ScanCcwConst') and (len(parameters)==1)):
                _ch = parameters[0]
                _mode = '0D'
                _rt = dc.Ctl_Scan(_ch,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'ScanCcwHome') and (len(parameters)==1)):
                _ch = parameters[0]
                _mode = '1F'
                _rt = dc.Ctl_Scan(_ch,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'ScanCw') and (len(parameters)==1)):
                _ch = parameters[0]
                _mode = '0E'
                _rt = dc.Ctl_Scan(_ch,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'ScanCwConst') and (len(parameters)==1)):
                _ch = parameters[0]
                _mode = '0C'
                _rt = dc.Ctl_Scan(_ch,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt

            elif((command == 'ScanCwHome') and (len(parameters)==1)):
                _ch = parameters[0]
                _mode = '1E'
                _rt = dc.Ctl_Scan(_ch,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' : ' + _rt
            elif( command == 'Select' and (len(parameters)==2)):
                _ch = parameters[0]
                _mno = parameters[1]
                _rt = 'Ok:'
                try:
                    _mnoi = int(_mno)
                except ValueError:
                    _rt = 'Er: Bad parameter.'
                    destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
                if('Ok:' in _rt):    
                    if((_mnoi < 0) or (_mnoi > 15)):
                        _rt = 'Er: Bad parameter.'
                        destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
                    else:
                        _mnox = format(_mnoi,'X')
                        _rt = dc.Ctl_Select(_ch,_mnox)
                        destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
            elif( (command == 'SetFunction') and (len(parameters)==1)):
                _sd = parameters[0]
                _rt = 'Ok:'
                _rsts = dc.Ctl_SetFunction(_sd)
                if('Er:' in _rsts):
                    _rt = _rsts
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt 

            elif( (command == 'SetHold') and (len(parameters)==2)):
                _ch = parameters[0]
                _hld = parameters[1]
                _rt = dc.Ctl_SetHold(_ch,_hld)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
            elif((command == 'SetValue') and (len(parameters)==2)):
                _ch = parameters[0]
                _sd = parameters[1]
                _dist = 'ABS'
                _rt = dc.Ctl_SetValue(_ch,_sd,_dist)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif((command == 'SetValueREL') and (len(parameters)==2)):
                _ch = parameters[0]
                _sd = parameters[1]
                _dist = 'REL'
                _rt = dc.Ctl_SetValue(_ch,_sd,_dist)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif( message == 'SpeedHigh'):
                _spf = '3'
                _rt = dc.Ctl_Speed(_spf)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
            elif( message == 'SpeedLow'):
                _spf = '1'
                _rt = dc.Ctl_Speed(_spf)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt
            elif( message == 'SpeedMiddle'):
                _spf = '2'
                _rt = dc.Ctl_Speed(_spf)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

#            elif(( pm16cx == 'on' ) and (command == 'SpeedMiddle')):
#                rt = ''
#                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + rt

            elif( message == 'Standby'):
                _rt = dc.Ctl_Standby()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif( message == 'Stop'):
                _rt = dc.Ctl_Stop()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + ' ' + _rt

            elif( (command == 'Stop') and (len(parameters)==1)):
                _ch = parameters[0]
                _rt = dc.Ctl_Stop(ch=_ch)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif( message == 'StopEmergency'):
                _rt = dc.Ctl_Stop(mode='1')
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif((command == 'StopEmergency') and (len(parameters)==1)):
                _ch = parameters[0]
                _rt = dc.Ctl_Stop(ch=_ch,mode='1')
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif( message == 'SyncRun'):
                _rt = dc.Ctl_SyncRun()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt

            elif( message == 'GetPause'):
                _rt = dc.Ctl_GetPause()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + _rt


##########
            elif((command == 'SendRawCommand' and parameter != '') and (gb_SRawC == True)):
                if('?' in parameter):
                    rt=dc.device_act(parameter)
                else:
                    rt=dc.device_send(parameter)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
###########
            elif((command == 'SRawCa' and parameter != '') and (gb_SRawC == True)):
                rt = dc.device_act(parameter)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
            elif((command == 'SRawCw' and parameter != '') and (gb_SRawC == True)):
                rt = dc.device_send(parameter)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + rt
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

    ####################################
    #      Device exclusive control    #
    ####################################
    def isbusyflgCtl(ctld):
        _fctl = 'System _ChangedCtlIsBusy ' + ctld
        st.send(_fctl)
        return

#################################################################################
#                               <<<<<<<<<<<<<<<<<<    Function definition       #
#################################################################################

 	##################################################################    
    # Define program arguments
    ##################################################################
    optIO=pystarsutilargparser.PyStarsUtilArgParser(numberOfDeviceServer=1)
    parser=optIO.generate_baseparser(prog=gb_ScriptName,version=__version__)
    ##################################################################
    # Parse program arguments
    ##################################################################
    args=parser.parse_args()
    gb_Debug=args.debug
    
    gb_SRawC = args.sendrawcommand      #20220829

    if(gb_Debug==True):
        sys.stdout.write(str(args)+'\n')

    starsNodeName = optIO.get(args.StarsNodeName,None)
    if( starsNodeName == 'pm16c04' or starsNodeName == 'pm16c021' or starsNodeName == 'pm16c4x'):
        supportdevice = 'yes'
    if( supportdevice == 'no'):
        _rt = 'Sorry, the input model is not supported. Please check the model.'
        sys.stdout.write(_rt +'\n')
        exit(1)

    configFileName = optIO.get(args.Config,None)
    
    if( configFileName is None):
        _rt = 'There is no specification of the config file, and the device cannot be specified'
        sys.stdout.write(_rt +'\n')
        exit(1)




    cfgIO = pystarsutilconfig.PyStarsUtilConfig(configFileName, gb_Debug, starsNodeName)
  

    if(cfgIO.gethandle() is None):
        sys.stdout.write(cfgIO.getlasterrortext()+'\n')
        exit(1)
    if(gb_Debug == False):
        gb_Debug        = cfgIO.get(starsNodeName, 'Debug'          , gb_Debug, bool)
    starsServerHost = cfgIO.get(starsNodeName, 'StarsServerHost', starsServerHost)
    starsServerPort = cfgIO.get(starsNodeName, 'StarsServerPort', starsServerPort, int)
    deviceHost      = cfgIO.get(starsNodeName, 'DeviceHost'     , deviceHost)
    devicePort      = cfgIO.get(starsNodeName, 'DevicePort'     , devicePort, int)
    motorname       = cfgIO.get(starsNodeName, 'MotorName'     , motorname)
    # Fix optional parameters
    starsServerHost = optIO.get(args.StarsServerHost,starsServerHost)
    starsServerPort = optIO.get(args.StarsServerPort,starsServerPort)
    deviceHost      = optIO.get(args.DeviceHost,deviceHost)
    devicePort      = optIO.get(args.DevicePort,devicePort)
#    motorname       = optIO.get(args.MotorName,motorname)

    gb_MotorNameList = motorname.split(' ')


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
    dc=PyStarsDevice_pm16c(deviceHost, devicePort)
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

# check device type
    _devtype = 'Er:'
    _cmd = 'VER?'
    _cdv = dc.device_act(_cmd)
    if(('PM16C-04X' in _cdv) and (starsNodeName == 'pm16c4x')):
        gb_pm16cx = 'on'
        _devtype = 'Ok:'
    elif(('PM16C-04' in _cdv) and (starsNodeName == 'pm16c04')):
        _devtype = 'OK:'
    elif(('PM16C-02' in _cdv) and (starsNodeName == 'pm16c021')):
        _devtype = 'Ok:'
    else:
        _rt =  _devtype + ' ' + 'different the device type. Please check the model.' 
        sys.stdout.write(_rt +'\n')
        exit(1)

# temporarily for debug pm16c = 'off' 
#    gb_pm16cx = 'off'

# device information check 
    dc.pm16c_flushdata()
    _stsA = dc.Ctl_IsBusy('A')
    _stsB = dc.Ctl_IsBusy('B')
    _stsC = dc.Ctl_IsBusy('C')
    _stsD = dc.Ctl_IsBusy('D')
    if((_stsA == '1') or (_stsB == '1') or (_stsC == '1') or (_stsD == '1')):
        gb_Interval_Time = INTERVAL_RUN

    #Start Mainloop()
#for check into mainloop

    print('\n' + '  <<<<<< main loop start >>>>>>  ' + '\n')       #for making sure 20220905


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
