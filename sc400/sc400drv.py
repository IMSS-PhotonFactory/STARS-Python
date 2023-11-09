#! /usr/bin/python3
"""
   STARS python program for Sc400 made by KOHZU seiki
    Description: Connect to STARS server and commnicate with the device.
    History:
       0.0     Base program written by Yasuko Nagatani
       1.0     2023.03.06   Beta     Hahsimoto Yoshiaki
       1.1     2023.03.     Brushup
""" 
## Define: program info
__author__ = 'Hashimoto Yoshiaki'

__version__ = '1.1'


__date__  = '2023-03-06'
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


class PyStarsDevice_sc400(nportserv.nportserv):
    """ Class PyStarsDevice_xxxx   _xxxx; device name
    """
    ##################################################################
    #                      Device control functions                  #
    ##################################################################
    #    data transfer function    #
    ################################
    ## Device send
    def device_send(self,cmd):
        if(self.isconnected()==False):
            return 'Er : Disconnected'
        _stx = chr(2)
        _cmd = _stx + cmd
        rt=self.send(_cmd)
        if(rt==False):
            return 'Er : ' + dc.getlasterrortext()
        self._deviceCommandLastExecutedTime = time.time()
        return 'Ok:'

    ## Device act
    def device_act(self,cmd,timeout=''):
        rt=self.device_send(cmd)
        if('Er :' in rt):
            return(rt)
        rt=self.device_receive(timeout)
        return rt

    ## Device receive
    def device_receive(self,timeout=''):
        if(timeout==''):
            timeout=self.gettimeout()
        rt=self.receive(timeout)
        if(rt is None):
            return('Er : '+self.error)
        if(rt == ''):
            return('Er : Timeout.')
        return rt

    #################################
    #     device reset functions    #
    #################################

    ############################################
    #    Command table manegement functions    #
    ############################################

################ 20220826
    def is_commanddefined(self,category,starscommand):
        _ctf = category
        _tf = 0
        if( _ctf == 'Controller'):
            if(starscommand in self._deviceCTLSTARSCommand):
                _tf = 1
        elif( _ctf == 'Motor'):
            if(starscommand in self._deviceMOTSTARSCommand):
                _tf = 2
        elif( _ctf == 'Encoder'):
            if(starscommand in self._deviceENCODERSTARSCommand):
                _tf = 3
        return(_tf)

    def get_commandlist(self,category):
        _ctf = category
        clist = []
        clist1 = []
        clist2 = []
        clist3 = []

        clist1 = self._deviceCTLSTARSCommand.keys()
        clist2 = self._deviceMOTSTARSCommand.keys()
        clist3 = self._deviceENCODERSTARSCommand.keys()

        if( _ctf == 'Controller'):
            for ck1 in clist1:
                _target = self._deviceCTLSTARSCommand[ck1]['Target']
                if( _target == 'Controller'):
                    clist.append(ck1)
        elif( _ctf == 'Motor'):
            for ck2 in clist2:
                _target = self._deviceMOTSTARSCommand[ck2]['Target']
                if( _target == 'Motor'):
                    clist.append(ck2)
        elif( _ctf == 'Encoder'):
            for ck3 in clist3:
                _target = self._deviceMOTSTARSCommand[ck3]['Target']
                if( _target == 'Motor'):
                    clist.append(ck3)
        return(clist)


    def get_commandhelp(self, tblflg, starscommand):
        rt='-'
        if(tblflg == 0):
            rt= ' Er: Nonexistent command.'
        elif(tblflg == 1):
            rt=self._deviceCTLSTARSCommand[starscommand]['help']
        elif(tblflg == 2):
            rt=self._deviceMOTSTARSCommand[starscommand]['help']
        elif(tblflg == 3):
            rt=self._deviceENCODERSTARSCommand[starscommand]['help']
        return(rt)

    def get_commandusage(self, tblflg, starscommand):
        rt='-'
        if(tblflg == 0):
            rt= ' Er: Nonexistent command.'
        elif(tblflg == 1):
            rt=self._deviceCTLSTARSCommand[starscommand]['Usage']
        elif(tblflg == 2):
            rt=self._deviceMOTSTARSCommand[starscommand]['Usage']
        elif(tblflg == 3):
            rt=self._deviceENCODERSTARSCommand[starscommand]['Usage']
        return(rt)


########################################################################
#####              sc400  StarsCommand  Description                ##### 
########################################################################
###################################################################
#   common function
###################################################################
#
    def axisno2mname(self,an):
        _axisno = an
        _rsts = self.axisno2mn(_axisno)
        if(_rsts is not None):
            rt = _rsts
        else:
            rt = 'Er: No match.'
        return(rt)

    def axisno3ename(self,an):
        _axisno = an
        _rsts = self.axisno2en(_axisno)
        if(_rsts is not None):
            rt = _rsts
        else:
            rt = 'Er: No match.'
        return(rt)

    def axisno2mn(self,an):
        global gb_NumberOfAxis
        _axisno = an
        _numaxi = gb_NumberOfAxis
        try:
            _axisnoi = int(_axisno)
        except ValueError:
            rt = 'Er: Bad Axis number.'
            return(rt)
        if((_axisnoi >= 1) and (_axisnoi <= _numaxi)):
            _mni = _axisnoi - 1
            rt = str(_mni)
        else:
            rt = 'Er: Bad Axis number.'
        return(rt)
        
    def mn2axisno(self,mn):
        global gb_NumberOfAxis
        _mno = mn
        _numaxi = gb_NumberOfAxis
        try:
            _mnoi = int(_mno)
        except ValueError:
            rt = 'Er: Bad Motor number.'
            return(rt)
        if((_mnoi >= 0) and (_mnoi < _numaxi)):
            _axi = _mnoi + 1
            rt = str(_axi)
        else:
            rt = 'Er: Bad Motor number.'
        return(rt)

    def mn2mname(self,mn):
        global gb_NumberOfAxis
        global gb_MotorNameList
        _mno = mn
        _numaxi = gb_NumberOfAxis
        _motorNameL = gb_MotorNameList
        try:
            _mnoi = int(_mno)
        except ValueError:
            rt = 'Er: Bad Motor number.'
            return(rt)
        if((_mnoi >= 0) and (_mnoi < _numaxi)):
            rt = _motorNameL[_mnoi]
        else:
            rt = 'Er: Bad Motor number.'
        return(rt)

    def mn2ename(self,mn):
        global gb_NumberOfAxis
        global gb_EncoderNameList
        _mno = mn
        _numaxi = gb_NumberOfAxis
        _encoderNameL = gb_EncoderNameList
        try:
            _mnoi = int(_mno)
        except ValueError:
            rt = 'Er: Bad Encoder number.'
            return(rt)
        if((_mnoi >= 0) and (_mnoi < _numaxi)):
            rt = _encoderNameL[_mnoi]
        else:
            rt = 'ER: Bad Encoder number.'
        return(rt)

    def mname2mn(self,mname):
        global gb_Motor2Ch
        rt = gb_Motor2Ch[mname]
        return(rt)

    def ename2en(self,ename):
        global gb_Encoder2Ch
        rt = gb_Encoder2Ch[ename]
        return(rt)

    def chkint(self,val):
        _data = val
        try:
            rt = int(_data)
        except ValueError:
            rt = 'Er: not int.'
        return(rt)


#=========================================================================================
###################################################################
#   sc_function
###################################################################

# sc send cmd
    def sc_sendcmd(self,func,cmd,cond):         # for sc400
        _fnc = func
        _cmd = cmd
        _cond = cond
        _rt = 'Er:'
#        _rtc = ', during[' + _cmd + ']execution in ' + _fnc + ' command.'
        _rtc = ''
        rt = 'Ok:'
        _rst = self.device_act(_cmd)
        if(_rst == ''):
            rt = _rt + ' Replay is null data ' + _rtc
            return(rt)
        elif('Er:' in _rst):
            return(_rst)
        _rplyd = _rst.split('\t',2)
        if((_rplyd[0] == 'C') and (_rplyd[1] == _cond)):
            if(len(_rplyd) > 2):
                rt = _rplyd[2]
            else:
                rt = 'Ok:'
        elif(_rplyd[0] == 'E'):
            rt = _rt + ' Error ' + _rplyd[2] + _rtc
        elif(_rplyd[0] == 'W'):
            rt = _rt + ' Worning ' + _rplyd[2] + _rtc
        elif(len(_rplyd) < 2):
            rt = _rt + ' Incorrect reply data.'
        else:
            if(_rplyd[1] == (_cond + '0')):
                rt = _rplyd[2]
            else:
                rt = _rt + ' System error ' + _rtc
        return(rt)

    def sc_getsysinfo(self,mn,frmi,endi,vf):
        _mn = mn
        _frmNOi = frmi
        _endNOi = endi + 1
        _vflg = vf
        _cmd = 'RSY'
        _axisno = self.mn2axisno(_mn)
        _sysinfo = ''
        if('Er:' in _axisno):
            return(_axisno)
        
        for v in range(_frmNOi,_endNOi):
            _fnc = 'sc_getsysinfo'
            _scom = _cmd + _axisno + '/' + str(v)
            _cond = _cmd + _axisno
            _dsts = self.sc_sendcmd(_fnc,_scom,_cond)
            if('Er:' in _dsts):
                rt = 'NA ' + _dsts
                return(rt)
            _dstsd = _dsts.split('\t')
            if(_vflg == 1):
                _sysinfo = _sysinfo + ',' + _dstsd[1]
            else:
                _sysinfo = _sysinfo + ',' + _dstsd[0] + ':' + _dstsd[1]
        rt = _sysinfo.lstrip(',')
        return(rt)

    def sc_isbusy(self,mn):
        global gb_devicename
        global gb_Flg_LimitStatus
        global gb_LimitStatusEnable
        if('.' in gb_devicename):
            _devname = gb_devicename.split('.')[0]
        else:
            _devname = gb_devicename
        _rt = 'Er:'
        rt = 'Ok:'
        _flgLS = gb_Flg_LimitStatus
        _lsenb = gb_LimitStatusEnable
        _mno = mn
        _axisno = self.mn2axisno(_mno)
        if('Er:' in _axisno):
            rt = _axisno
            return(rt)
        _rsts = self.sc_getstatus(_axisno,'ADE')
        if('Er:' in _rsts):
            rt = _rsts
        else:
            _rstsT = _rsts.split(',')
            _drvtype = _rstsT[0]
            if(len(_rstsT) == 3):
                _cwlsi = int(_rstsT[1])
                _ccwlsi = int(_rstsT[2])
                _ls = str(_cwlsi + _ccwlsi*2)
                if(_flgLS[int(_mno)] != _ls):
                    if(_lsenb == True):
                        _destsendstr =  str(_devname) + '.' + str(self.axisno2mname(_axisno))  + '>System _ChangedLimitStatus ' + _ls
                        st.send(_destsendstr)
                    gb_Flg_LimitStatus[int(_mno)] = _ls
            else:
                rt = _rt + ' Undecidable data.'
                return(rt)
            try:
                _drvti = int(_drvtype)
            except ValueError:
                rt = _rt + ' Undecidable data.'
                return(rt)
            if(_drvti == 0):
                rt = '0'
            elif((_drvti >=1) and (_drvti <= 3)):
                rt = '1'
            else:
                rt = _rt + ' Undecidable data.'
        return(rt)

    def sc_getstatus(self,num,req = 'full'):
        _axisn = num
        _request = req
        _cmd = 'STR'
        _mode = '1'
        _rt = 'Er:'
        rt = 'Ok:'
        _dstsr = [None,None,None,None,None,None,None,None]
        _gsts = []
        _rplyd = ''

        if(_request == 'full'):
            _dstsr = ['sts','sts','sts','sts','sts','sts','sts','sts']
        else:
            for x in _request:
                _pli = int(ord(x) - ord('A'))
                if((_pli < 0) or (_pli) > 9):
                    rt = _rt + ' Bad request.'
                    return(rt)
                _dstsr[_pli+1] = 'sts'
        _func = 'getstatus'
        _cmdl = _cmd + _mode + '/' + _axisn
        _cond = _cmd + _axisn
        _rsts = self.sc_sendcmd(_func,_cmdl,_cond)
        if('Er:' in _rsts):
            rt = _rsts
            return(rt)
        _gsts = _rsts.split('\t')
        if(_gsts[0] != '1'):
            rt = _rt + 'Bad reply data.'
        for v in range(1,8):
            if(_dstsr[v] is not None):
                _rplyd = _rplyd + ',' + _gsts[v]
        if(rt == 'Ok:'):
            rt = _rplyd.lstrip(',')
        return(rt)

    def sc_getvalue(self,mn,tg,md):
        _axisno = self.mn2axisno(mn)
        _target = tg
        _mode = md
        _fnc = 'sc_getvalue'
        _cond = 'RD' + _target + _axisno
        _cmd = _cond + '/' + _mode
        _rsts = self.sc_sendcmd(_fnc,_cmd,_cond)
        return(_rsts)


    def sc_setpreset(self,mno,tg,sv):
        global gb_PCHK
        _mno = mno
        _axisno = self.mn2axisno(_mno)
        _target = tg
        _setvalue = sv
        _mode = 'Preset'
        _cmd = 'WR' + _target + _axisno + '/' + _setvalue
        _cond = 'WR' + _target + _axisno
        _ck0 = self.sc_checkbusyoff(_mno)
        if('Ok:' not in _ck0):
            rt = _ck0
            return(rt)
        _ck1 = self.sc_checkstandbyoff()
        if('Er:' in _ck1):
            rt = _ck1
            return(rt)
        if(gb_PCHK == True):
            _ck2 = self.sc_checkpulse(_setvalue,_mode)
            if('Er:' in _ck2):
                rt = _ck2
                return(rt)
        _rsts = self.sc_sendcmd('sc_setpreset',_cmd,_cond)
        rt = _rsts
        return(rt)

    def sc_Stop(self,mn,stmd):         # for sc400
        _mn = mn
        _mode = stmd
        _cmd = 'STP'

        if(_mn == '-1'):
            _axisno = '0'
        else:
            _axisno = self.mn2axisno(_mn)
            if(_axisno == ''):
                return
        _fnc = 'sc_stop'
        _sncmd = _cmd + _axisno + '/' + _mode
        _cond = _cmd + _axisno
        _rst = self.sc_sendcmd(_fnc,_sncmd,_cond)
        return(_rst)

    def sc_reset_syncrun(self):        # for sc400
        global gb_SyncMPSCommand
        global gb_SyncRunTimes
        gb_SyncRunTimes = -1        #SYNC_RUN_TIME = -1
        gb_SyncMPSCommand = None
        return('Ok: Standby is off.')

    def sc_checkpulse(self,sv,md):
        _setvalue = sv
        _type = md
        _rt = 'Er:'
        rt = 'Ok:'
        try:
            _setvaluei = int(_setvalue)
        except ValueError:
            rt = _rt  + ' Bad parameter.'
            return(rt)
        if(_type == 'DR'):
            _rangeL = -16777215
            _rangeH = 16777215
            _type = 'Data'
        else:       # md == 'Preset', 'set_offset', 
            _rangeL = -68108813
            _rangeH = 68108813
        if((_setvaluei < _rangeL) or (_setvaluei > _rangeH)):
            rt = _rt + 'Bad parameter. ' + _type + ' Out of Range.'
        return(rt)
    def sc_checkstandbyoff(self):      # for sc400
        global gb_SyncRunTimes
        if(gb_SyncRunTimes >= 0):
            _rt = 'Er: Standby is already on.'
        else:
            _rt = 'Ok: Standby is off'
        return(_rt)
    def sc_checkbusyoff(self,mno):
        _mno = mno
        rt = ''
        _bsts = self.sc_isbusy(_mno)
        if('Er:' in _bsts):
            rt = _bsts
        elif(_bsts == '1'):
            rt = 'Busy'
        elif(_bsts == '0'):
            rt = 'Ok:'
        else:
            rt = 'Er: System Error.'
        return(rt)
        

####################################
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>#
###################################################################
#   interval processing
###################################################################

    def interval(self):
        global gb_Interval_Time
        global gb_Buf_Interval
        global gb_Flg_Busy
        global gb_NumberOfAxis
        global gb_MotorPositionFMT
        global gb_EncoderPositionFMT
        global gb_Position
        global gb_Encoder
        global gb_devicename
        global gb_2Dext

        _mpFMT = gb_MotorPositionFMT
        _enFMT = gb_EncoderPositionFMT
        _position = gb_Position
        _encoder = gb_Encoder
        _numaxisi = int(gb_NumberOfAxis)
        _busyN = 0
        _rt = 'ER:'
        rt = 'Ok:'

        if('.' in gb_devicename):
            _devname = gb_devicename.split('.')[0]
        else:
            _devname = gb_devicename
        if(gb_Interval_Time == INTERVAL_STOP):
            for v in range(0,_numaxisi):
                vs = str(v)
                _ckbusy = self.sc_isbusy(vs)
                if(_ckbusy == '1'):
                    _mname = self.mn2mname(vs)
                    _destsendstr =  str(_devname) + '.' + _mname  + '>System _ChangedIsBusy 1'
                    st.send(_destsendstr)
                    gb_Flg_Busy[v] = '1'
                    gb_Interval_Time = INTERVAL_RUN
                elif(_ckbusy == '0'):
                    continue
                else:
                    rt = _rt + ' Fatal Error1.'
                    sys.exit(rt)
            gb_Buf_Interval -= 1
            if(gb_Buf_Interval <= 1):
                for v in range(0,_numaxisi):
                    vs = str(v)
                    _mname = self.mn2mname(vs)
                    _ename = self.mn2ename(vs)
                    _mpf = _mpFMT[v]
                    _epf = _enFMT[v]
                    _mpd = self.sc_getvalue(vs,'P',_mpf)
                    if(_mpd != _position[v]):
                        _destsendstr =  str(_devname) + '.' + _mname  + '>System _ChangedValue ' + _mpd
                        st.send(_destsendstr)
                        gb_Position[v] = _mpd
                    _epd = self.sc_getvalue(vs,'E',_epf)
                    if(_epd != _encoder[v]):
                        _destsendstr =  str(_devname) + '.' + _ename  + '>System _ChangedValue ' + _epd
                        st.send(_destsendstr)
                        gb_Encoder[v] = _epd
                gb_Buf_Interval = REFRESH_RUN/INTERVAL_RUN
            return('Ok:')
        gb_Buf_Interval -= 1
        if(gb_Buf_Interval <= 0):
            for v in range(0,_numaxisi):
                if(gb_Flg_Busy[v] == '1'):
                    vs = str(v)
                    _mname = self.mn2mname(vs)
                    _ename = self.mn2ename(vs)
                    _mpf = _mpFMT[v]
                    _epf = _enFMT[v]
                    _mpd = self.sc_getvalue(vs,'P',_mpf)
                    _destsendstr =  str(_devname) + '.' + _mname  + '>System _ChangedValue ' + _mpd
                    st.send(_destsendstr)
                    gb_Position[v] = _mpd
                    _epd = self.sc_getvalue(vs,'E',_epf)
                    _destsendstr =  str(_devname) + '.' + _ename  + '>System _ChangedValue ' + _epd
                    st.send(_destsendstr)
                    gb_Encoder[v] = _epd
            gb_Buf_Interval = REFRESH_RUN/INTERVAL_RUN
        for v in range(0,_numaxisi):
            if(gb_Flg_Busy[v] == '1'):
                _busyN += 1
        for v in range(0,_numaxisi):
            vs = str(v)
            if(gb_Flg_Busy[v] == '1'):
                _ckbusy = self.sc_isbusy(vs)
                if(_ckbusy == '0'):
                    if(_busyN == 1):
                        gb_Interval_Time = INTERVAL_STOP
                    _mname = self.mn2mname(vs)
                    _ename = self.mn2ename(vs)
                    _mpf = _mpFMT[v]
                    _epf = _enFMT[v]
                    _mpd = self.sc_getvalue(vs,'P',_mpf)
                    _destsendstr =  str(_devname) + '.' + _mname  + '>System _ChangedValue ' + _mpd
                    st.send(_destsendstr)
                    gb_Position[v] = _mpd
                    _epd = self.sc_getvalue(vs,'E',_epf)
                    _destsendstr =  str(_devname) + '.' + _ename  + '>System _ChangedValue ' + _epd
                    st.send(_destsendstr)
                    gb_Encoder[v] = _epd
                    _destsendstr =  str(_devname) + '.' + _mname  + '>System _ChangedIsBusy 0'
                    st.send(_destsendstr)
                    gb_Flg_Busy[v] = '0'
                    _busyN -= 1
                elif(_ckbusy == '1'):
                    continue
                else:
                    rt = _rt + ' Fatal Error2.'
                    sys.exit(rt)
        return
###################################################################
#   Motor command execution procedure
###################################################################
    def Motor_AccModeSelect(self,mno,am):
        global gb_DefaultAccMode
        _rt = 'Er:'
        rt = 'Ok:'
        try:
            _ami = int(am)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_ami < 1) or (_ami > 5)):
            rt = _rt + ' Bad parameter.'
        if('Er:' in rt):
            return(rt)
        gb_DefaultAccMode[int(mno)] = am
        return(rt)
    def Motor_GetAccModeSelected(self,mno):
        global gb_DefaultAccMode
        rt = gb_DefaultAccMode[int(mno)]
        return(rt)
    def Motor_BacklashModeSelect(self,mno,bm):
        global gb_DefaultBacklachMode
        global gb_NumberOfAxis
        _rt = 'Er:'
        rt = 'Ok:'
        try:
            _bmi = int(bm)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_bmi < 0) or ( 4 < _bmi)):
            rt = _rt + ' Bad parameter.'
        if('Er:' in rt):
            return(rt)
        gb_DefaultBacklachMode[int(mno)] = bm
        return(rt)
    def Motor_GetBacklashModeSelected(self,mno):
        global gb_DefaultBacklachMode
        rt = gb_DefaultBacklachMode[int(mno)]
        return(rt)
    def Motor_GetAxisNumber(self,mno):
        _mno = mno
        rt = self.mn2axisno(_mno)
        return(rt)
    def Motor_EncoderCorrectModeSelect(self,mno,em):
        global gb_DefaultEncoderCorrectMode
        _rt = 'Er:'
        rt = 'Ok:'
        try:
            _emi = int(em)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_emi < 0) or (_emi > 2)):
            rt = _rt + ' Bad parameter.'
        if('Er:' in rt):
            return(rt)
        gb_DefaultEncoderCorrectMode[int(mno)] = em
        return(rt)
    def Motor_GetEncoderCorrectModeSelected(self,mno):
        global gb_DefaultEncoderCorrectMode
        rt = gb_DefaultEncoderCorrectMode[int(mno)]
        return(rt)
    def Motor_GetHomePositionCorrectModeSelected(self,mno):
        global gb_DefaultOrgMode
        rt = gb_DefaultOrgMode[int(mno)]
        return(rt)
    def Motor_HomePositionCorrectModeSelect(self,mno,hpcm):
        global gb_DefaultOrgMode
        _rt = 'Er:'
        rt = 'Ok:'
        try:
            _hpcmi = int(hpcm)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_hpcmi < 1) or (_hpcmi > 17)):
            rt = _rt + ' Bad parameter.'
        if('Er:' in rt):
            return(rt)
        gb_DefaultOrgMode[int(mno)] = hpcm
        return(rt)
    def Motor_GetLimitStatus(self,mno):
        global gb_Flg_LimitStatus
        _mno = mno
        _rsts = self.sc_isbusy(_mno)
        if('Er:' in _rsts):
            rt = _rsts
        else:
            rt = gb_Flg_LimitStatus[int(_mno)]
        return(rt)
    def Motor_GetOffset(self,mno):
        _mno = mno
        _axisno = self.mn2axisno(_mno)
        if(_axisno == ''):
            return('Er: No axisnumber.')
        _fnc = 'sc_getoffset'
        _cmd = 'RDO' + _axisno
        _cond = _cmd
        _rsts = self.sc_sendcmd(_fnc,_cmd,_cond)
        rt = _rsts
        return(rt)
    def Motor_GetSpeedTblInfo(self,mno,ln):
        _mno = self.mn2axisno(mno)
        _rt = 'Er:'
        rt = 'Ok:'
        _fnc = 'sc_getspdtblinfo'

        try:
            _tblno = int(ln)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        if(_tblno == 0):
            _cmd = 'RMS' + _mno
            _cond = _cmd
            _rsts = self.sc_sendcmd(_fnc,_cmd,_cond)
            _rply = _rsts.split('\t')
            _stinfo = '- ' + _rply[0] + ' ' + _rply[1] + ' ' + _rply[2] + ' ' + _rply[3] + ' ' + _rply[13] + ' ' + _rply[14]
            rt = _stinfo
        elif((_tblno >= 1) and (_tblno <= 11)):
            _cmd = 'RTB' + _mno + '/' + ln
            _cond = 'RTB' + _mno
            _rsts = self.sc_sendcmd(_fnc,_cmd,_cond)
            _rply = _rsts.split('\t')
            try:
                _tbni = int(_rply[0])
            except ValueError:
                rt = _rt + ' Bad replydata 1 excuting in ' + _fnc + '.'
                return(rt)
            if(_rply[0] != ln):
                rt = _rt + ' Bad replydata 2 excuting in ' + _fnc + '.'
            else:
                rt = _rply[1] + ' ' + _rply[2] + ' ' + _rply[3] + ' ' + _rply[4] + ' ' + _rply[5] + ' ' + _rply[6] + ' ' + _rply[7]
        else:
            rt = _rt + ' Bad parameter.'
        return(rt)
    def Motor_GetSpeedTblNoSelected(self,mno):
        global gb_DefaultSpeedTBlNo
        rt = gb_DefaultSpeedTBlNo[int(mno)] 
        return(rt)
    def Motor_GetStatus(self,mno):
        _axisno = self.mn2axisno(mno)
        _rsts = self.sc_getstatus(_axisno,)
        return(_rsts)
    def Motor_GetSysInfo(self,mno,par,mf):
        _mno = mno
        _par = []
        _devsys = mf
        _parln = 2
        _rt = 'Er:'
        rt = 'Ok:'
        if(par == 'full'):
            par = '1-' + _devsys
        if('-' in par):
            _par = par.split('-')
            _parln = len(_par)
        else:
            _par = par
            _parln = 1
        if(_parln == 1):
            try:
                _par0i = int(_par)
            except ValueError:
                rt = _rt + ' Bad parameter.'
                return(rt)
            if(_devsys == '47'):
                if((_par0i < 1) or (_par0i > 47)):
                    rt = _rt + ' Bad parameter.'
                    return(rt)
            else:
                if((_par0i < 1) or (_par0i > 52)):
                    rt = _rt + ' Bad parameter.'
                    return(rt)
            _rplyd = self.sc_getsysinfo(_mno,_par0i,_par0i,'0')
            rt = _rplyd
        if(_parln == 2):
            try:
                _par0i = int(_par[0])
                _par1i = int(_par[1])
            except ValueError:
                rt = _rt + ' Bad parameter.'
                return(rt)
            if(_devsys == '47'):
                if((_par0i < 1) or (_par0i > 47) or (_par1i < 1) or (_par1i > 47)):
                    rt = _rt + ' Bad parameter.'
                    return(rt)
            else:
                if((_par0i < 1) or (_par0i > 52 or (_par1i < 1) or (_par1i > 52))):
                    rt = _rt + ' Bad parameter.'
                    return(rt)
            _rplyd = self.sc_getsysinfo(_mno,_par0i,_par1i,'0')
            rt = _rplyd
        return(rt)

    def Motor_GetValue(self,mno,md):
        _mno = mno
        _tg = 'P'
        _mode = md
        _rt = 'Er:'
        rt = 'Ok:'
        try:
            _mdi = int(_mode)
        except ValueError:
            rt = 'Er: Bad parameter'
            return(rt)
        if(rt == 'Ok:'):
            if((_mdi < 0) or (_mdi > 3)):
                rt = _rt + ' Bad parameter'
            else:
                _rsts = dc.sc_getvalue(_mno,_tg,_mode)
                rt = _rsts
        return(rt)

    def Motor_ScanHome(self,mno,acm,sym,spt,org):
        global gb_devicename
        global gb_Flg_Busy
        global gb_Interval_Time
        if('.' in gb_devicename):
            _devname = gb_devicename.split('.')[0]
        else:
            _devname = gb_devicename
        _mno = mno
        _mnoi = int(_mno)
        _axisno = self.mn2axisno(_mno)
        _acdmode = acm
        _syncmode = sym
        _sptbl = spt
        _orgm = org
        _rt = 'Er:'
        rt = 'Ok:'

        try:
            _acdmodei = int(_acdmode)
            _syncmodei = int(_syncmode)
            _sptbli = int(_sptbl)
            _orgmi = int(_orgm)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_orgmi < 1) or (_orgmi > 17)):
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_acdmodei < 1) or (_acdmodei > 5)):
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_syncmodei < 0) or (_syncmodei > 1)):
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_sptbli < 0) or (_sptbli > 9)):
            rt = _rt + ' Bad parameter.'
            return(rt)
        _bsyfck = self.sc_checkbusyoff(_mno)
        if(_bsyfck != 'Ok:'):
            rt = _bsyfck
            return(rt)
        _stbck = self.sc_checkstandbyoff()
        if('Er:' in _stbck):
            rt = _stbck
            return(rt)
        _fnc = 'sc_scanhome'
        _cond = 'ORG' + _axisno 
        _cmd = _cond + '/' + _acdmode + '/' + _syncmode + '/' +  _sptbl + '/' + _orgm + '/' + '1'
        _rsts = self.sc_sendcmd(_fnc,_cmd,_cond)
        if('Er:' in _rsts):
            rt = _rsts
        else:
            _destsendstr =  str(_devname) + '.' + str(self.mn2mname(_mno)) + '>System _ChangedBusy 1'
            st.send(_destsendstr)
            gb_Flg_Busy[_mnoi] = '1'
            gb_Interval_Time = INTERVAL_RUN
        return(rt)

    def Motor_SetLink(self,mno,slv1, dr1, slv2, dr2):
        global gb_MotorNameList
        _axisMno = self.mn2axisno(mno)
        _slvmotor1 = slv1
        _depratio1 = dr1
        _slvmotor2 = slv2
        _depratio2 = dr2
        _axisSno1 = None
        _axisSno2 = None
        _sflg = '1'
        _rt = 'Er:'
        rt = 'Ok:'

        if(_slvmotor1 not in gb_MotorNameList):
            rt = _rt + ' Bad parameter.'
            return(rt)
        else:
            try:
                _ratcki = int(_depratio1)
            except ValueError:
                rt = _rt + ' Bad parameter.'
                return(rt)
        if((_ratcki < 1) or (_ratcki > 255)):
            rt = _rt + ' Bad dependency ratio'
            return(rt)
        _mn1 = self.mname2mn(_slvmotor1)
        _axisSno1 = self.mn2axisno(_mn1)
        if(((slv2 is not None) and (dr2 is not None))):
            if(_slvmotor2 not in gb_MotorNameList):
                rt = _rt + ' Bad parameter.'
                return(rt)
            try:
                _ratcki = int(_depratio2)
            except ValueError:
                rt = _rt + ' Bad parameter.'
                return(rt)
            if((_ratcki < 1) or (_ratcki > 255)):
                rt = _rt + ' Bad dependency ratio'
                return(rt)
            _mn2 = self.mname2mn(_slvmotor2)
            _axisSno2 = self.mn2axisno(_mn2)
            _sflg = '2'
        _fnc = 'sc_setlink'
        _cond = 'LNK' + _axisMno
        _cmd = _cond + '/' + _axisSno1 + '/' + _depratio1
        if(_sflg == '2'):
            _cmd = _cmd + '/' + _axisSno2 + '/' + _depratio2
        _rsts = self.sc_sendcmd(_fnc,_cmd,_cond)
        rt = _rsts
        return(rt)
        
    def Motor_SetOffset(self,mno,sv):
        global gb_PCHK
        _mno = mno
        _setvalue = sv
        _rt = 'Er:'
        rt = 'Ok:'
        try:
            _svi = int(sv)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        _axisno = self.mn2axisno(_mno)
        _ckf0 = self.sc_checkbusyoff(_mno)
        if('Ok:' not in _ckf0):
            rt = _ckf0
            return(rt)
        _ckf1 = self.sc_checkstandbyoff()
        if('Ok:' not in _ckf1):
            rt = _ckf1
            return(rt)
        if(gb_PCHK == True):
            _ckf2 = self.sc_checkpulse(_setvalue,'set_offset')
            if('Ok:' not in _ckf2):
                rt =_ckf2
                return(rt)
        _fnc = 'sc_setoffset'
        _cond = 'WRO' + _axisno
        _cmd = _cond + '/' + _setvalue
        _rsts  = self.sc_sendcmd(_fnc,_cmd,_cond)
        if('Er:' in _rsts):
            rt = _rsts
        return(rt)

    def Motor_SetSpeedTblInfo(self,mno,spt,sts,tps,atm,dtm):
        global gb_PCHK
        _mno = mno
        _sptblno = spt
        _stspd = sts
        _mxspd = tps
        _acctm = atm
        _dctm = dtm
        _rt = 'Er:'
        try:
            _tbni = int(_sptblno)
        except ValueError:
            rt = _rt + ' Bad Speed table number.'
            return(rt)
        if((_tbni < 1) or (11 < _tbni)):
            rt = _rt + ' Bad Speed table number.'
            return(rt)
        if(gb_PCHK == True):
            try:
                _sspi = int(_stspd)
                _mspi = int(_mxspd)
                _ati = int(_acctm)
                _dti = int(_dctm)
            except ValueError:
                rt = _rt + ' Bad Parameter.'
                return(rt)
            if((_sspi < 1) or (_sspi > 4095500)):
                rt = _rt + ' Start Speed is out of range.'
                return(rt)
            if((_mspi < 1) or (_mspi > 4095500)):
                rt = _rt + ' Max Speed is out of range.'
                return(rt)
            if((_ati < 1) or (_ati > 1000000)):
                rt = _rt + ' Acceleration time is out of range.'
                return(rt)
            if((_dti < 1) or (_dti > 1000000)):
                rt = _rt + ' Deceleration time is out of range.'
                return(rt)
        _axisno = self.mn2axisno(_mno)
        rt = 'Ok:'
        _fnc = 'sc_setspdtblinfo'
        _cond = 'WTB' + _axisno
        _cmd = _cond + '/' + _sptblno + '/' + _stspd + '/' + _mxspd + '/' + _acctm + '/' + _dctm
        _rsts = self.sc_sendcmd(_fnc,_cmd,_cond)
        if('Er:' in _rsts):
            rt = _rsts
        return(rt)

    def Motor_SetSysTblInfoASI(self,mno,sts,tps,atm,dtm,op,prsc,bcor,deno,mol,pcy,lmsmd):
        global gb_PCHK
        _rt = 'Er:'
        _mno = mno
        _stspd = sts
        _mxspd = tps
        _acctime = atm
        _dctime = dtm
        _oposi = op
        _prsc = prsc
        _bclcor = bcor
        _pdenomi = deno
        _pmole = mol
        _pcary = pcy
        _lmspmode = lmsmd
        if(gb_PCHK == True):
            try:
                _sspi = int(_stspd)
                _mspi = int(_mxspd)
                _ati = int(_acctime)
                _dti = int(_dctime)
                _opi = int(_oposi)
                _pci = int(_prsc)
                _bci = int(_bclcor)
                _pdi = int(_pdenomi)
                _pmi = int(_pmole)
                _poi = int(_pcary)
            except ValueError:
                rt = _rt + ' Bad parameter'
                return(rt)
            if((_sspi < 1) or (_sspi > 4095500)):
                rt = _rt + ' Start Speed is out of range.'
                return(rt)
            if((_mspi < 1) or (_mspi > 4095500)):
                rt = _rt + ' Max Speed is out of range.'
                return(rt)
            if((_ati < 1) or (_ati > 1000000)):
                rt = _rt + ' Acceleration time is out of range.'
                return(rt)
            if((_dti < 1) or (_dti > 1000000)):
                rt = _rt + ' Deceleration time is out of range.'
                return(rt)
            if((_opi < -1677215) or (_opi > 1677215)):
                rt = _rt + ' Position data is out of range.'
                return(rt)
            if((_pci < 0) or (_pci > 1677215)):
                rt = _rt + ' Prescale data is out of range.'
                return(rt)
            if((_bci < 0) or (_bci > 1677215)):
                rt = _rt + ' Backlash compensation value is out of range.'
                return(rt)
            if((_pdi < 1) or (_pdi > 1677215)):
                rt = _rt + ' Denominator of the conversion factor is out of range.'
                return(rt)
            if((_pmi < 1) or (_pmi > 1677215)):
                rt = _rt + ' Numerator of the conversion factor is out of range.'
                return(rt)
            if((_poi < 0) or (_poi > 9)):
                rt = _rt + ' Carry specification set value is out of range.'
                return(rt)
        if((_lmspmode != '0') and (_lmspmode != '1')):
            rt = _rt + ' Bad parameter.'
            return(rt)
        _axisno = self.mn2axisno(_mno)
        rt = 'Ok:'
        _fnc = 'sc_setsystblinfoasi'
        _cond = 'ASI' + _axisno
        _cmd = _cond + '/' + _stspd + '/' + _mxspd + '/' + _acctime + '/' + _dctime + '/' + _oposi + '/' + _prsc + '/' + _bclcor + '/' + _pdenomi + '/' + _pmole + '/0/0/' + _pcary + '/' + _lmspmode
        _rsts = self.sc_sendcmd(_fnc,_cmd,_cond)
        if('Er:' in _rsts):
            rt = _rsts
        return(rt)

    def Motor_SetValue(self,mno,tp,acm,syncm,spt,bcor,ecor):
        global gb_devicename
        global gb_Flg_Busy
        global gb_Interval_Time
        global gb_SyncRunTimes
        global gb_NumberOfAxis
        global gb_SyncMPSCommand
        global gb_PCHK
        _syncrtimei = gb_SyncRunTimes
        _numofaxisi = gb_NumberOfAxis
        _syncmpsccom = gb_SyncMPSCommand
        if('.' in gb_devicename):
            _devname = gb_devicename.split('.')[0]
        else:
            _devname = gb_devicename
        _mno = mno
        _tposi = tp
        _accmode = acm
        _syncmode = syncm
        _sptblno = spt
        _bclcor = bcor
        _enccor = ecor
        _rt = 'Er:'
        if(gb_PCHK == True):
            _stck1 = self.sc_checkpulse(_tposi,'Data')
            if(_stck1 != 'Ok:'):
                rt= _stck1
                return(rt)
        try:
            _acmi = int(_accmode)
            _stbi = int(_sptblno)
            _bcmi = int(_bclcor)
            _ecci = int(_enccor)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_acmi < 1) or (_acmi > 5)):
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_syncmode != '0') and (_syncmode != '1')):
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_stbi < 0) or (_stbi > 9)):
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_bcmi < 0) or (_bcmi > 4)):
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_ecci < 0) or (_ecci > 2)):
            rt = _rt + ' Bad parameter.'
            return(rt)

        _currentposition = self.sc_getvalue(_mno,'P','0')
        _chkvaluei = int(_currentposition) - int(_tposi)
        if((_chkvaluei < -16777215) or (_chkvaluei > 16777215)):
            rt = _rt + ' Target value is outside the operating range.'
            return(rt)

        _mpsccomlck = 0
        _chkax = ''
        _parm = ''
        _axisno = self.mn2axisno(_mno)
        _mname = self.mn2mname(_mno)
        _cmd0 = 'APS'
        rt = 'Ok:'

        _stck0 = self.sc_checkbusyoff(_mno)
        if(_stck0 != 'Ok:'):
            rt = _stck0
            return(rt)
        if(_syncrtimei >= 0):
            if(_syncrtimei >= _numofaxisi):
                rt = _rt + ' SetValue Excuse Over Max.'
                return(rt)
            elif(_syncrtimei == 0):
                gb_SyncMPSCommand = _axisno + '/' + _tposi
            else:
                _syncmpsccom = _syncmpsccom.lstrip('/')
                _mpscomck = _syncmpsccom.split('/')
                if(len(_mpscomck) >= 2):
                    _chkax = _mpscomck[0]
                if(len(_mpscomck) >= 4):
                    _chkax = _chkax + ',' + _mpscomck[2]
                if(len(_mpscomck) == 6):
                    _chkax = _chkax + ',' + _mpscomck[4]
                _mpsccomlck = (len(_syncmpsccom.split('/')))/2
                if(_syncrtimei != _mpsccomlck):
                    rt = _rt + ' Invalid syncrun param.'
                    return(rt)
                if(_axisno in _chkax):
                    rt = _rt + ' Motor ' + _mname + ' is already assigned to syncrun.'
                    return(rt)
                gb_SyncMPSCommand = gb_SyncMPSCommand + '/' + _axisno + '/' + _tposi
            _parm = _accmode + '/' + _syncmode + '/' + _sptblno + '/?/' + _bclcor + '/' + _enccor + '/1'
            gb_SyncRunTimes += 1
        else:
            _parm = _accmode + '/' + _syncmode + '/' + _sptblno + '/' + _tposi + '/' + _bclcor + '/' + _enccor + '/1'
        _fnc = 'sc_setvalue'
        _cond = _cmd0 + _axisno
        _cmd = _cond + '/' + _parm
        _rsts = self.sc_sendcmd(_fnc,_cmd,_cond)
        if(_rsts == 'Ok:'):
            if(gb_SyncRunTimes < 0):
                _destsendstr =  str(_devname) + '.' + _mname + '>System _ChangedIsBusy 1'
                st.send(_destsendstr)
                gb_Flg_Busy[int(_mno)] = '1'
                gb_Interval_Time = INTERVAL_RUN
#            return(rt)
        elif(('Er:' in _rsts) and ('Worning 1' in _rsts)):
            if(gb_SyncRunTimes < 0):
                _destsendstr =  str(_devname) + '.' + _mname + '>System _ChangedIsBusy 1'
                st.send(_destsendstr)
                gb_Flg_Busy[int(_mno)] = '1'
                gb_Interval_Time = INTERVAL_RUN
#            return(rt)
        else:
            rt = _rsts
        return(rt)

    def Motor_SetValueREL(self,mno,tp,acm,syncm,spt,bcor,ecor):
        global gb_devicename
        global gb_Flg_Busy
        global gb_Interval_Time
        global gb_SyncRunTimes
        global gb_NumberOfAxis
        global gb_SyncMPSCommand
        global gb_PCHK
        _syncrtimei = gb_SyncRunTimes
        _numofaxisi = gb_NumberOfAxis
        _syncmpsccom = gb_SyncMPSCommand
        _rt = 'Er:'

        if('.' in gb_devicename):
            _devname = gb_devicename.split('.')[0]
        else:
            _devname = gb_devicename
        _mno = mno
        _tposi = tp
        _accmode = acm
        _syncmode = syncm
        _sptblno = spt
        _bclcor = bcor
        _enccor = ecor
        _mpsccomlck = 0
        _chkax = ''
        _parm = ''

        if(gb_PCHK == True):
            _stck1 = self.sc_checkpulse(_tposi,'DR')
            if(_stck1 != 'Ok:'):
                rt= _stck1
                return(rt)
        try:
            _acmi = int(_accmode)
            _stbi = int(_sptblno)
            _bcmi = int(_bclcor)
            _ecci = int(_enccor)
        except ValueError:
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_acmi < 1) or (_acmi > 5)):
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_syncmode != '0') and (_syncmode != '1')):
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_stbi < 0) or (_stbi > 9)):
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_bcmi < 0) or (_bcmi > 4)):
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_ecci < 0) or (_ecci > 2)):
            rt = _rt + ' Bad parameter.'
            return(rt)

        _axisno = self.mn2axisno(_mno)
        _mname = self.mn2mname(_mno)
        _cmd0 = 'RPS'
        rt = 'Ok:'

        _stck0 = self.sc_checkbusyoff(_mno)
        if(_stck0 != 'Ok:'):
            rt = _stck0
            return(rt)
        if(_syncrtimei >= 0):
            _cmd0 = 'APS'
            if(_syncrtimei >= _numofaxisi):
                rt = _rt + ' SetValue Excuse Over Max.'
                return(rt)
            elif(_syncrtimei == 0):
                _plsckDbn = self.sc_getvalue(_mno,'P','0')
                _plsckDn = str(int(_tposi) + int(_plsckDbn))
                if(gb_PCHK == True):
                    _plsckn = self.sc_checkpulse(_plsckDn,'Data')
                    if(_plsckn != 'Ok:'):
                        rt = _plsckn
                        return(rt)
                gb_SyncMPSCommand = _axisno + '/' + _plsckDn
            else:
                _syncmpsccom = _syncmpsccom.lstrip('/')
                _mpscomck = _syncmpsccom.split('/')
                if(len(_mpscomck) >= 2):
                    _chkax = _mpscomck[0]
                if(len(_mpscomck) >= 4):
                    _chkax = _chkax + ',' + _mpscomck[2]
                if(len(_mpscomck) == 6):
                    _chkax = _chkax + ',' + _mpscomck[4]
                _mpsccomlck = (len(_syncmpsccom.split('/')))/2
                if(_syncrtimei != _mpsccomlck):
                    rt = _rt + ' Invalid syncrun param.'
                    return(rt)
                if(_axisno in _chkax):
                    rt = _rt + ' Motor ' + _mname + ' is already assigned to syncrun.'
                    return(rt)
                _plsckDb0 = self.sc_getvalue(_mno,'P','0')
                _plsckD0 = str(int(_tposi) + int(_plsckDb0))
                if(gb_PCHK == True):
                    _plsck0 = self.sc_checkpulse(_plsckD0,'Data')
                    if(_plsck0 != 'Ok:'):
                        rt = _plsck0
                        return(rt)
                gb_SyncMPSCommand = gb_SyncMPSCommand + '/' + _axisno + '/' + _plsckD0
            _parm = _accmode + '/' + _syncmode + '/' + _sptblno + '/?/' + _bclcor + '/' + _enccor + '/1'
            gb_SyncRunTimes += 1
        else:
            _plsckDb = self.sc_getvalue(_mno,'P','0')
            _plsckD = str(int(_plsckDb) + int(_tposi))
            print(' >>> Point-SVR300 _plsckD = ' + _plsckD + '\n')
            if(gb_PCHK == True):
                _plsck = self.sc_checkpulse(_plsckD,'Data')
                if(_plsck != 'Ok:'):
                    rt = _plsck0
                    return(rt)
            _parm = _accmode + '/' + _syncmode + '/' + _sptblno + '/' + _tposi + '/' + _bclcor + '/' + _enccor + '/1'
        _fnc = 'sc_setvalueREL'
        _cond = _cmd0 + _axisno
        _cmd = _cond + '/' + _parm
        _rsts = self.sc_sendcmd(_fnc,_cmd,_cond)
        if(_rsts == 'Ok:'):
            if(gb_SyncRunTimes < 0):
                _destsendstr =  str(_devname) + '.' + _mname + '>System _ChangedIsBusy 1'
                st.send(_destsendstr)
                gb_Flg_Busy[int(_mno)] = '1'
                gb_Interval_Time = INTERVAL_RUN
            return(rt)
        elif(('Er:' in _rsts) and ('Worning 1' in _rsts)):
            if(gb_SyncRunTimes < 0):
                _destsendstr =  str(_devname) + '.' + _mname + '>System _ChangedIsBusy 1'
                st.send(_destsendstr)
                gb_Flg_Busy[int(_mno)] = '1'
                gb_Interval_Time = INTERVAL_RUN
            return(rt)
        else:
            rt = _rsts
        return(rt)

    def Motor_SpeedTblNoSelect(self,mno,tbn):
        global gb_DefaultSpeedTBlNo
        _mnoi = int(mno)
        _spdtblno = tbn
        rt = 'Ok'
        try:
            _ckdi = int(_spdtblno)
        except ValueError:
            rt = 'Er: Bad parameter.'
            return(rt)
        if((_ckdi <0) or (_ckdi > 9)):
            rt = 'Er: Bad parameter.'
            return(rt)
        gb_DefaultSpeedTBlNo[_mnoi] = _spdtblno
        return(rt)

###################################################################
#   Encoder command execution procedure
###################################################################
    def Encoder_GetAxisNumber(self,eno):
        _eno = eno
        _rsts = self.mn2axisno(_eno)
        rt = _rsts
        return(rt)

    def Encoder_GetValue(self,eno,md):
        _eno = eno
        _mode = md
        _rsts = self.sc_getvalue(_eno,'E',_mode)
        rt = _rsts
        return(rt)

    def Encoder_Preset(self,eno,sv):
        global gb_devicename
        global gb_Encoder
        global gb_EncoderPositionFMT
        if('.' in gb_devicename):
            _devname = gb_devicename.split('.')[0]
        else:
            _devname = gb_devicename
        _encoderFMT = gb_EncoderPositionFMT
        _eno = eno
        _enoi = int(_eno)
        _setvalue = sv
        rt = 'Ok:'
        _rsts = self.sc_setpreset(_eno,'E',_setvalue)
        if('Er:' in _rsts):
            rt = _rsts
            return(rt)
        else:
            _mode = _encoderFMT[_enoi]
            _ename = self.mn2ename(_eno)
            _rpd = self.sc_getvalue(_eno,'E',_mode)
            _destsendstr =  str(_devname) + '.' + _ename + '>System _ChangedValue ' + str(_rpd)
            st.send(_destsendstr)
            gb_Encoder[_enoi] = _rpd
        return(rt)

    def Encoder_GetInfo(self,eno):
        _func = 'encoder_getinfo'
        _axisn = self.mn2axisno(eno)
        _com = 'RES' + _axisn
        _cont = _com
        _rstinfo = self.sc_sendcmd(_func,_com,_cont)
        if('Er:' in _rstinfo):
            _rt = _rstinfo
        else:
            _rsts = _rstinfo.split('\t')
            _rt = _rsts[1] + ' ' + _rsts[2] + ' ' + _rsts[3] + ' ' + _rsts[4] + ' ' + _rsts[5] + ' ' + _rsts[6] + ' ' + _rsts[8] + ' ' + _rsts[9]
        return(_rt)

    def Encoder_SetInfo(self,eno,par,ct):
        global gb_PCHK
        _rt = 'Er:'
        _func = 'encoder_setinfo'
        _axisn = self.mn2axisno(eno)
        _par = par.split(' ')

        if(gb_PCHK == True):
            try:
                _denoi = int(_par[0])
                _molei = int(_par[1])
                _pscli = int(_par[2])
            except ValueError:
                rt = _rt + ' Bad parameter.'
                return(rt)
            if((_denoi < 1) or (_denoi > 1677215)):
                rt = _rt + ' Data is out of range.'
                return(rt)
            if((_molei < 1) or (_molei > 1677215)):
                rt = _rt + ' Data is out of range.'
                return(rt)
            if((_pscli < 0) or (_pscli > 1677215)):
                rt = _rt + ' Data is out of range.'
                return(rt)
        if((_par[3] != '1') and (_par[3] != '2') and (_par[3] != '4')):
            rt = _rt + ' Bad parameter.'
            return(rt)
        if((_par[4] != '0') and (_par[4] != '1')):
            rt = _rt + ' Bad parameter.'
            return(rt)
        _cont = 'ESI' + _axisn
        if( ct == 'R'):
            _com = _cont + '/0/' + _par[0] + '/' + _par[1] + '/' + _par[2] + '/' + _par[3] + '/' + _par[4]
        else:
            if(gb_PCHK == True):
                try:
                    _rtcti = int(_par[5])
                    _pndti = int(_par[6])
                    _encri = int(_par[7])
                except ValueError:
                    rt = _rt + ' Bad parameter.'
                    return(rt)
                if((_rtcti < 1) or (_rtcti > 10000)):
                    rt = _rt + ' Data is out of range.'
                    return(rt)
                if((_pndti < 1) or (_pndti > 10000)):
                    rt = _rt + ' Data is out of range.'
                    return(rt)
                if((_encri < 0) or (_encri > 9)):
                    rt = _rt + ' Data is out of range.'
                    return(rt)


            _com = _cont + '/0/' + _par[0] + '/' + _par[1] + '/' + _par[2] + '/' + _par[3] + '/' + _par[4] + '/' + _par[5] + '/1/' + _par[6] + '/' + _par[7]
        _rst = self.sc_sendcmd(_func,_com,_cont)
        return(_rst)

###################################################################
#   Ctl command execution procedure
###################################################################

    def Ctl_flushdata(self,frm=None):            # for sc400
        global gb_devicename
        global gb_NumberOfAxis
        global gb_Flg_remote                # : 0 -> Local, 1 -> remote, but remote only
        global gb_Flg_Busy
        global gb_LimitStatusEnable         # : False => not enable, True -> enable
        global gb_Flg_LimitStatus
        global gb_MotorPositionFMT
        global gb_EncoderPositionFMT
        global gb_Position
        global gb_Encoder

        if('.' in gb_devicename):
            _devname = gb_devicename.split('.')[0]
        else:
            _devname = gb_devicename
        _fbsy = gb_Flg_Busy
        _flg_remotelocal = gb_Flg_remote
        _numberOfAxis = gb_NumberOfAxis
        _flg_LS_Enable = gb_LimitStatusEnable
        _LimitStatus = gb_Flg_LimitStatus
        _mpositionFMT = gb_MotorPositionFMT
        _epositionFMT = gb_EncoderPositionFMT
        _axisni = int(_numberOfAxis)
##   
        if(frm == None):
            _from = 'System'
        else:
            _from = frm
        rt = 'Ok:'
        _changeFun = _from + ' _ChangedFunction '
        _changeIB = _from + ' _ChangedIsBusy '
        _changeLS = _from + ' _ChangedLimitStatus '
        _changeVal = _from + ' _ChangedValue '

#
        _destsendstr = _devname + '>' + _changeFun + _flg_remotelocal
        st.send(_destsendstr)
#
        for v in range(_axisni):
            _cht = '.ch'
            _rst = self.sc_isbusy(v)
            if( 'Er:' in _rst):          # Changed the description that was 'nE' to '0' 
                return(_rst)
            _destsendstr =  _devname + _cht + str(v) + '>' + _changeIB + _rst
            st.send(_destsendstr)
            _fbsy[v] = _rst
            if(_flg_LS_Enable == True):
                _destsendstr =  str(_devname) + _cht + str(v) + '>' + _changeLS + _LimitStatus[v]
                st.send(_destsendstr)
            _tg = 'P'
            _cht = '.ch'
            _mp = self.sc_getvalue(str(v), _tg , _mpositionFMT[v])
            gb_Position[v] = _mp
            _destsendstr =  str(_devname) + _cht + str(v) + '>' + _changeVal + _mp
            st.send(_destsendstr)
            _tg = 'E'
            _cht = '.enc'
            _ep = self.sc_getvalue(str(v), _tg, _epositionFMT[v])
            gb_Encoder[v] = _ep
            _destsendstr =  str(_devname) + _cht + str(v) + '>' + _changeVal + _ep
            st.send(_destsendstr)
        gb_Flg_Busy = _fbsy
        return(rt)

    def Ctl_Standby(self, md):
        global gb_SyncRunTimes
        _mode = md
        rt = 'Ok:'
        if(_mode == '1'):
            _rsts = self.sc_checkstandbyoff()
            if('Er:' in _rsts):
                return(_rsts)
            gb_SyncRunTimes = 0
        elif(_mode == '0'):
            rt = self.sc_reset_syncrun()
        else:
            rt = 'Er: Bad parameter.'
        return(rt)            

    def Ctl_SyncRun(self):
        global gb_SyncMPSCommand
        global gb_SyncRunTimes
        global gb_NumberOfAxis
        global gb_Flg_Busy
        global gb_Interval_Time
        global gb_devicename

        if('.' in gb_devicename):
            _devname = gb_devicename.split('.')[0]
        else:
            _devname = gb_devicename


        _mpscmd = gb_SyncMPSCommand
        _numaxisi = gb_NumberOfAxis
        _flg_busy = gb_Flg_Busy
        _cmd = 'MPS'
        _termmpsc = []
        rt = 'Ok:'
        if(gb_SyncRunTimes < 0):
            rt = 'Er: Standby Off.'
        elif(gb_SyncRunTimes == 0):
            rt = 'Er: SetValue Not Executed.'
        elif(gb_SyncRunTimes == 1):
            rt = 'Er: SetValue 1 time Exceuted.'
        else:
            _fnc = 'syncrun'
            _scmd = _cmd + _mpscmd + '/' + '1'
            _cond = _scmd.split('/')[0]
            _rst = self.sc_sendcmd(_fnc,_scmd,_cond)
            if(_rst == 'Ok:'):
                if('/' in _mpscmd):
                    _termmpsc = _mpscmd.split('/')
                    if(len(_termmpsc) > 3):
                        _mn0i = int(_termmpsc[0]) - 1
                        _mn1i = int(_termmpsc[2]) - 1
                        _maxis0 = self.mn2mname(str(_mn0i))
                        _maxis1 = self.mn2mname(str(_mn1i))
                        _flg_busy[_mn0i] = '1'
                        _destsendstr =  str(_devname) + '.' + _maxis0 + '>System _ChangedIsBusy 1'
                        st.send(_destsendstr)
                        _flg_busy[_mn1i] = '1'
                        _destsendstr =  str(_devname) + '.' + _maxis1 + '>System _ChangedIsBusy 1'
                        st.send(_destsendstr)
                    if(len(_termmpsc) > 5):
                        _mn2i = int(_termmpsc[4]) - 1
                        _maxis2 = self.mn2mname(str(_mn2i))
                        _flg_busy[_mn2i] = '1'
                        _destsendstr =  str(_devname) + '.' + _maxis2 + '>System _ChangedIsBusy 1'
                        st.send(_destsendstr)
                    if(len(_termmpsc) > 7):
                        _mn3i = int(_termmpsc[6]) - 1
                        _maxis3 = self.mn2mname(str(_mn3i))
                        _flg_busy[_mn3i] = '1'
                        _destsendstr =  str(_devname) + '.' + _maxis3 + '>System _ChangedIsBusy 1'
                        st.send(_destsendstr)
                else:
                    for v in range(_numaxisi):
                        _flg_busy[v] = self.sc_isbusy(v)
                gb_Flg_Busy = _flg_busy
                gb_Interval_Time = INTERVAL_RUN
            elif(_rst != ''):
                rt = 'Er: SYS' + str(_rst) + ' IN sc_syncrun.'
        self.sc_reset_syncrun()
        return(rt)
#=========================================================================================
##########################################################################################
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
        lc_deviceENCODERSTARSCommand = {}
#        lc_MotorSpeed = []
#        lc_MotorSpeedRate = []
#        lc_AccelarationRate = []
###############################################
#          << Common Command >>    #          #
#---------------------------------------------#
#        lc_deviceComSTARSCommand['GetAccRateList']                         ={"Target":"Common","Usage":"GetAccRateList","help":"Get list of settable motor acceleration rate."}
#        lc_deviceComSTARSCommand['GetSpeedList']                           ={"Target":"Common","Usage":"GetSpeedList","help":"Get list of settable motor speed."}
#        lc_deviceComSTARSCommand['getversion']                             ={"Target":"Common","Usage":"getversion","help":"Return this program version."}
#        lc_deviceComSTARSCommand['hello']                                  ={"Target":"Common","Usage":"hello","help":"The client returns \@hello nice to meet you.\""}
###############################################
#         << Standard Event Command >>        #
#---------------------------------------------#
        lc_deviceComSTARSCommand['_ChangedIsBusy']                         ={"Target":"Event", "help":"_ChangedIsBusy event shows that the status of motor has been changed. 1 is busy, 0 is free."}
        lc_deviceComSTARSCommand['_ChangedLimitStatus']                    ={"Target":"Event", "help":"_ChangedLimitStatus event shows that the status of limit-signal of CW|CCW has been changed."}
        lc_deviceComSTARSCommand['_ChangedValue']                          ={"Target":"Event", "help":"_ChangedValue event shows that the position of motor or encoder has been changed."}
        lc_deviceComSTARSCommand['_ChangedFunction']                       ={"Target":"Event", "help":"_ChangedFunction event event shows that the function has been changed. 1 is Remote, 0 is Local."}
###############################################
#      << Standard Controller Command >>      #
#---------------------------------------------#
        lc_deviceCTLSTARSCommand['flushdata']                              ={"Target":"Controller","Usage":"flushdata","help":"By using the command, all the status information of the controller, motor and encoder will be sent to the Stars server as an event message."}
        lc_deviceCTLSTARSCommand['flushdatatome']                          ={"Target":"Controller","Usage":"flushdatatome","help":"By using the command, event messages for all controllers, motors, and encoders will be displayed."}
        lc_deviceCTLSTARSCommand['GetControllerName']                      ={"Target":"Controller","Usage":"GetControllerName","help":"Use the command to show the name of the connected device's controller."}
        lc_deviceCTLSTARSCommand['GetDeviceName']                          ={"Target":"Controller","Usage":"GetDeviceName","help":"Use the command to show the name of the connected device."}
        lc_deviceCTLSTARSCommand['GetEncoderList']                         ={"Target":"Controller","Usage":"GetEncoderList","help":"Use the command to show the list of configured encoders."}
        lc_deviceCTLSTARSCommand['GetEncoderName']                         ={"Target":"Controller","Usage":"GetEncoderName axis_number","help":"Use the command to get the name of the encoder corresponding to the axis number."}
        lc_deviceCTLSTARSCommand['GetFunction']                            ={"Target":"Controller","Usage":"GetFunction","help":"Use the command to indicate where the device is in remoto state (=1) or local state (=0)."}
        lc_deviceCTLSTARSCommand['GetMachineName']                         ={"Target":"Controller","Usage":"GetMachineName","help":"Use the command show the name of the connected machine."}
        lc_deviceCTLSTARSCommand['GetMotorList']                           ={"Target":"Controller","Usage":"GetMotorList","help":"Use the command to show the list of configured motors."}
        lc_deviceCTLSTARSCommand['GetMotorName']                           ={"Target":"Controller","Usage":"GetMotorName axis_number","help":"Use the command to get the name of the motor corresponding to the axis number."}
        lc_deviceCTLSTARSCommand['GetRomVersion']                          ={"Target":"Controller","Usage":"GetRomVersion","help":"Use the command tp get the version of the control program for the connected device."}
        lc_deviceCTLSTARSCommand['GetVersion']                             ={"Target":"Controller","Usage":"getversion","help":"Use the command to display the version of this program."}
        lc_deviceCTLSTARSCommand['hello']                                  ={"Target":"Controller","Usage":"hello","help":"The client returns \@hello nice to meet you.\""}
        lc_deviceCTLSTARSCommand['SendRawCommand']                         ={"Target":"Controller","Usage":"SendRawCommand device_command","help":"Used to directly execute device commands."}
        lc_deviceCTLSTARSCommand['SetFunction']                            ={"Target":"Controller","Usage":"SetFunction 1|0","help":"Use the command to set function (Remote=1, Local=0).However, this device cannot be in the local state."}
        lc_deviceCTLSTARSCommand['Standby']                                ={"Target":"Controller","Usage":"Standby","help":"Use the command to suspend the motor drive for multi-axis drive."}
        lc_deviceCTLSTARSCommand['Stop']                                   ={"Target":"Controller","Usage":"Stop","help":"Use the command to stop all motors."}
        lc_deviceCTLSTARSCommand['StopEmergency']                          ={"Target":"Controller","Usage":"StopEmergency","help":"Use the command to stop stop of all motors Emergency."}
        lc_deviceCTLSTARSCommand['SyncRun']                                ={"Target":"Controller","Usage":"SyncRun","help":"Use the command to start driving the motor whose operation has been suspended."}
        lc_deviceCTLSTARSCommand['terminate']                              ={"Target":"Controller","Usage":"terminate","help":"Use the command to terminate device-client processing."}
        lc_deviceCTLSTARSCommand['Usage']                                  ={"Target":"Controller","Usage":"Usage stars_command","help":"Use the command to display how to use a command described in the argument."}

###############################################
#         << Standard Motor Command >>        #
#---------------------------------------------#

        lc_deviceMOTSTARSCommand['AccModeSelect']                          ={"Target":"Motor","Usage":"AccModeSelect 1-5","help":"Use the command to set the acceleration/deceleration mode."}
        lc_deviceMOTSTARSCommand['BacklashModeSelect']                     ={"Target":"Motor","Usage":"BacklashModeSelect 0-4","help":"Use the command to set the backlash mode."}
        lc_deviceMOTSTARSCommand['EncoderCorrectModeSelect']               ={"Target":"Motor","Usage":"EncoderCorrectModeSelect 0-2","help":"Use the command to set the encoder correct mode."}
        lc_deviceMOTSTARSCommand['GetAccModeSelected']                     ={"Target":"Motor","Usage":"GetAccModeSelected","help":"Use the command to show the acceleration/deceleration mode."}
        lc_deviceMOTSTARSCommand['GetAxisNumber']                          ={"Target":"Motor","Usage":"GetAxisNumber motor_name","help":"Use the command to get the axis number corresponding to the motor name."}
        lc_deviceMOTSTARSCommand['GetBacklashModeSelected']                ={"Target":"Motor","Usage":"GetBacklashModeSelected","help":"Use the command show the backlash mode."}
        lc_deviceMOTSTARSCommand['GetEncoderCorrectModeSelected']          ={"Target":"Motor","Usage":"GetEncoderCorrectModeSelected","help":"Use the command to show the encoder correct mode."}
        lc_deviceMOTSTARSCommand['GetHomePositionCorrectModeSelected']     ={"Target":"Motor","Usage":"GetHomePositionCorrectModeSelected","help":"Use the command to show the home position correct mode."}
        lc_deviceMOTSTARSCommand['GetLimitStatus']                         ={"Target":"Motor","Usage":"GetLimitStatus","help":"Use the command get the status of limit-signals of CW|CCW from the device."}
        lc_deviceMOTSTARSCommand['GetOffset']                              ={"Target":"Motor","Usage":"GetOffset","help":"Use the command to get the motor position offset value from the device."}
        lc_deviceMOTSTARSCommand['GetSpeedTblInfo']                        ={"Target":"Motor","Usage":"GetSpeedTblInfo table_number","help":"Use the command to get the speed table information from the device"}
        lc_deviceMOTSTARSCommand['GetSpeedTblNoSelected']                  ={"Target":"Motor","Usage":"GetSpeedTblNoSelected","help":"Use the command to show the selected speed table number."}
        lc_deviceMOTSTARSCommand['GetStatus']                              ={"Target":"Motor","Usage":"GetStatus","help":"Use the command to get the status of the motor from the device."}
        lc_deviceMOTSTARSCommand['GetSysInfo']                             ={"Target":"Motor","Usage":"GetSysInfo system_number","help":"Use the command to get system information from the device."}
        lc_deviceMOTSTARSCommand['GetValue']                               ={"Target":"Motor","Usage":"GetValue 0-3","help":"Use the command to get the current position of the  motor."}
        lc_deviceMOTSTARSCommand['HomePositionCorrectModeSelect']          ={"Target":"Motor","Usage":"HomePositionCorrectModeSelect [1-17]","help":"Use the command to set the home position correct mode."}
        lc_deviceMOTSTARSCommand['IsBusy']                                 ={"Target":"Motor","Usage":"IsBusy","help":"Use the command to check th current driving status of the motor."}
        lc_deviceMOTSTARSCommand['Preset']                                 ={"Target":"Motor","Usage":"Preset value","help":"Use the command to rewrite the current position of the motor."}
        lc_deviceMOTSTARSCommand['ScanHome']                               ={"Target":"Motor","Usage":"ScanHome [some arguments]","help":"Use the command to detect the origin position of the motor. Please check the reference manual for arguments."}
        lc_deviceMOTSTARSCommand['SetLink']                                ={"Target":"Motor","Usage":"SetLink motor_name operation_ratio","help":"Use the command to set the slave motor (one or two) and the operation ratio of the slave motor."}
        lc_deviceMOTSTARSCommand['SetOffset']                              ={"Target":"Motor","Usage":"SetOffset value","help":"Use the command to set the offset of the motor."}
        lc_deviceMOTSTARSCommand['SetSpeedTblInfo']                        ={"Target":"Motor","Usage":"SetSpeedTblInfo [some arguments]","help":"Use the command to set data to the speed table(No.1-No.11)."}
        lc_deviceMOTSTARSCommand['SetSysTblInfoASI']                       ={"Target":"Motor","Usage":"SetSysTblInfoASI [some arguments]","help":"Use the command to set data to the speed table(No.0)."}
        lc_deviceMOTSTARSCommand['SetValue']                               ={"Target":"Motor","Usage":"SetValue [some arguments]","help":"Use the command to move the position of th motor to the specified position(absoluto value)."}
        lc_deviceMOTSTARSCommand['SetValueREL']                            ={"Target":"Motor","Usage":"SetValueREL [some arguments]","help":"Use the command to move the position of th motor to the specified position(relative value)."}
        lc_deviceMOTSTARSCommand['SpeedTblNoSelect']                       ={"Target":"Motor","Usage":"SpeedTblNoSelect 0-9","help":"Use the command to set the speed table number to use."}
        lc_deviceMOTSTARSCommand['Stop']                                   ={"Target":"Motor","Usage":"Stop","help":"Use the command to stop the motor."}
        lc_deviceMOTSTARSCommand['StopEmergency']                          ={"Target":"Motor","Usage":"StopEmergency","help":"Use the command to stop the motor emergency."}
        lc_deviceMOTSTARSCommand['Usage']                                  ={"Target":"Motor","Usage":"Usage stars_command","help":"Use the command to display how to use a command described in the argument."}
###############################################
#  Standerd Encoder Command >> #
#---------------------------------------------#
        lc_deviceENCODERSTARSCommand['GetAxisNumber']                      ={"Target":"Encoder","Usage":"GetAxisNumber encoder_name","help":"Use the command to get the axis number corresponding to the motor name."}
        lc_deviceENCODERSTARSCommand['GetValue']                           ={"Target":"Encoder","Usage":"GetValue 0-3","help":"Use the command to get the current position of the encoder."}
        lc_deviceENCODERSTARSCommand['Preset']                             ={"Target":"Encoder","Usage":"Preset value","help":"Use the command to rewrite the current position of the encoder."}
        lc_deviceENCODERSTARSCommand['Usage']                              ={"Target":"Encoder","Usage":"Usage stars_command","help":"Use the command to display how to use a command described in the argument."}
###############################################
##########################################################################
#        self._deviceComSTARSCommand = lc_deviceComSTARSCommand
        self._deviceCTLSTARSCommand = lc_deviceCTLSTARSCommand
        self._deviceMOTSTARSCommand = lc_deviceMOTSTARSCommand
        self._deviceENCODERSTARSCommand = lc_deviceENCODERSTARSCommand

#        self._MotorSpeed = lc_MotorSpeed
#        self._MotorSpeedRate = lc_MotorSpeedRate
#        self._AccelarationRate = lc_AccelarationRate 

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
    gb_MotorNameList = []               # Assumed to be used in the motor name discribed comfig.cfg
    gb_EncoderNameList = []
    gb_DefaultAccMode = []              # SYS8
    gb_Flg_LimitStatus = []
    gb_DefaultBacklachMode = []         # SYS22
    gb_DefaultEncoderCorrectMode = []   # SYS29
    gb_DefaultOrgMode = []              # SYS9

    gb_DefaultSpeedTBlNo = ['0','0','0','0']

    gb_MotorPositionFMT = ['1','1','1','1']
    gb_EncoderPositionFMT = ['1','1','1','1']


    gb_NumberOfAxis = 1
    gb_NumberOfMotor = 0

    gb_Motor2Ch = {}
    gb_Encoder2Ch = {}

    gb_SyncMPSCommand = None

    gb_StarsInstance = None
    gb_DeviceInstance = None
    gb_userconfigfile = True                # 20220831
# for display informations to cliant windows
    gb_devicename = ''
    gb_cliant = ''
# Remote/Local ; 0:Local, 1:Remote
    gb_Flg_remote = '1'
# IsBusy flg    Changed the description that was nE to 0
    gb_Is_busyflg_ch0 = '0'
    gb_Is_busyflg_ch1 = '0'
    gb_Is_busyflg_ch2 = '0'
    gb_Is_busyflg_ch3 = '0'
    gb_Flg_Busy = [gb_Is_busyflg_ch0,gb_Is_busyflg_ch1,gb_Is_busyflg_ch2,gb_Is_busyflg_ch3]

# Event flg    
    gb_Is_eventsE_ch0 = 'ON'
    gb_Is_eventsE_ch1 = 'ON'
    gb_Is_eventsE_ch2 = 'ON'
    gb_Is_eventsE_ch3 = 'ON'

# Motor position
    gb_Position = [None,None,None,None,None,None,None,None]
# Encoder position
    gb_Encoder = [None,None,None,None,None,None,None,None]
# Information for Control
    gb_CancelBacklash = [None,None,None,None,None,None,None,None]
# SendRawCommandEnableFlg
    gb_SRawC = False
# LimitStatusEnableFlg
#    gb_LimitStatus = False
    gb_LimitStatusEnable = False        # False -> not enable, true -> enable
# SupportDeviceFlg
#    Eventually it will be set to sc200 or sc400. 
    gb_devtype = ''
    gb_devsysNo = '52'
    supportdevice = 'no'
    gb_DEVICE = ''
# Paremeter check enable
    gb_PCHK = True 
# constant for time control
    SYNC_RUN_TIME = 0
    gb_SyncRunTimes = SYNC_RUN_TIME

#
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
#    gb_Elaps = 0
    gb_Interval_Time = INTERVAL_RUN
    gb_Buf_Interval = REFRESH_RUN/INTERVAL_RUN
# 2drive extratime
    gb_2Dext = '0'

# Define: Appliction default parameters
    starsServerHost = 'localhost'
    starsNodeName   = 'tdkzplus'
    starsServerPort = 6057
    deviceHost = '172.16.0.53' #169.254.9.35
    devicePort = 7777  #8003
# 
    motorname = 'cho'
    encodername = 'enc0'
    motorname_list = []
    encodername_list = []

# need to access config.cfg     20220829
    configFileName = 'config.cfg'

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
        dc.interval()

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
# <- 20220316
#
        global gb_MotorNameList
        global gb_Motor2Ch
        global gb_EncoderNameList
        global gb_Encoder2Ch
        global gb_DefaultAccMode
        global gb_DefaultSpeedTBlNo
        global gb_DefaultBacklachMode
        global gb_DefaultEncoderCorrectMode
        global gb_DefaultOrgMode
## Remote/Local ; 0:Local, 1:Remote
        global gb_Flg_remote
        global gb_SRawC
#
        global gb_devicename
        global gb_cliant
#
        global gb_CancelBacklash
#
        global gb_Is_busyflg_ch0
        global gb_Is_busyflg_ch1
        global gb_Is_busyflg_ch2
        global gb_Is_busyflg_ch3

        global gb_Flg_Busy

        global gb_Is_eventsE_ch0
        global gb_Is_eventsE_ch1
        global gb_Is_eventsE_ch2
        global gb_Is_eventsE_ch3
#
#        global gb_Elaps
#
        dc = gb_DeviceInstance
        st = gb_StarsInstance
#
        motorlist = gb_MotorNameList
        motorCH = gb_Motor2Ch
        encoderlist = gb_EncoderNameList
        encoderCH = gb_Encoder2Ch
        defaccmode = gb_DefaultAccMode
        defbaclmode = gb_DefaultBacklachMode
        defenccormode = gb_DefaultEncoderCorrectMode
        defspdtbln = gb_DefaultSpeedTBlNo
        deforgmode = gb_DefaultOrgMode

#
        global gb_DEVICE
#
        global gb_devsysNo
        _devicesysno = gb_devsysNo
#
        Flg_Remote = gb_Flg_remote
#
        Flg_IsBusy = gb_Flg_Busy
        Flg_Event_ch0 = gb_Is_eventsE_ch0
        Flg_Event_ch1 = gb_Is_eventsE_ch1
        Flg_Event_ch2 = gb_Is_eventsE_ch2
        Flg_Event_ch3 = gb_Is_eventsE_ch3
        Flg_IsEvent = [Flg_Event_ch0,Flg_Event_ch1,Flg_Event_ch2,Flg_Event_ch3]


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
            _currentMNo = ''        # 0 to 3 for sc400
#            _currentMNox = ''      # Not required for sc400 
            _cmck = 'bad'
            _currentmotorencoder = allmess.nodeto.split('.')[1]
            _CME = _currentmotorencoder.upper()
            if('ENC' in _CME):
                _category = 'Encoder'
                _currentencoder = _currentmotorencoder
                _currentmotor = None
            else:
                _category = 'Motor'
                _currentmotor = _currentmotorencoder
                _currentencoder = None

        elif(allmess.nodeto == st.nodename):
            _category = 'Controller'
            _currentmotor = None
            _currentencoder = None        
        else:
            _category = None
            _currentmotor = None
            _currentencoder = None
            if(message.startswith('@')):
                return
            elif(message.startswith('_')):
                return
            else:
                destsendstr = st.nodename + '>' + allmess.nodefrom +' @' + message + ' Er: Bad node.'
            if(destsendstr != ''):
                _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
                rt=st.send(destsendstr)
            else:
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom +' @' + message + ' Er: Bad command or parameters.'

##############
        if(_category == 'Motor'):
            if( _currentmotor not in motorlist):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom + ' @' + message + ' ' + 'Er: The name of a motor that does not exist. '
                _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
                rt=st.send(destsendstr)
                return
            else:
                _currentMNo = motorCH[_currentmotor]
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
            elif(message == 'help'):
                clist1=sorted(dc.get_commandlist(_category))
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + ' '.join(clist1)
            elif(command == 'help' and len(parameters) == 1):
                _prm=parameters[0]
                _rt = dc.is_commanddefined(_category,_prm)
                if(_rt is None):
                    rt='Er: Command not found'
                else:
                    rt=dc.get_commandhelp(_rt,_prm)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(rt)   # str() 20220913
            elif(command == 'Usage' and len(parameters) == 1):
                _prm=parameters[0]
                _rt = dc.is_commanddefined(_category,_prm)
                if(_rt is None):
                    rt='Er: Command not found'
                else:
                    rt=dc.get_commandusage(_rt,_prm)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(rt)   # str() 20220913
            elif((command == 'AccModeSelect') and (len(parameters)== 1)):
                _mno = _currentMNo
                _ln = parameters[0]
                _rt = dc.Motor_AccModeSelect(_mno,_ln)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'BacklashModeSelect') and (len(parameters)== 1)):
                _mno = _currentMNo
                _ln = parameters[0]
                _rt = dc.Motor_BacklashModeSelect(_mno,_ln)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'EncoderCorrectModeSelect') and (len(parameters)== 1)):
                _mno = _currentMNo
                _ln = parameters[0]
                _rt = dc.Motor_EncoderCorrectModeSelect(_mno,_ln)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif(message == 'GetAccModeSelected'):
                _mno = _currentMNo
                _rt = dc.Motor_GetAccModeSelected(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'GetAxisNumber'):
                _mno = _currentMNo
                _rt = dc.Motor_GetAxisNumber(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'GetBacklashModeSelected'):
                _mno = _currentMNo
                _rt = dc.Motor_GetBacklashModeSelected(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'GetEncoderCorrectModeSelected'):
                _mno = _currentMNo
                _rt = dc.Motor_GetEncoderCorrectModeSelected(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'GetHomePositionCorrectModeSelected'):
                _mno = _currentMNo
                _rt = dc.Motor_GetHomePositionCorrectModeSelected(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'GetLimitStatus'):
                _mno = _currentMNo
                _rt = dc.Motor_GetLimitStatus(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'GetOffset'):
                _mno = _currentMNo
                _rt = dc.Motor_GetOffset(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif((command == 'GetSpeedTblInfo') and (len(parameters)== 1)):
                _mno = _currentMNo
                _ln = parameters[0]
                _rt = dc.Motor_GetSpeedTblInfo(_mno,_ln)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif(message == 'GetSpeedTblNoSelected'):
                _mno = _currentMNo
                _rt = dc.Motor_GetSpeedTblNoSelected(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'GetStatus'):
                _mno = _currentMNo
                _rt = dc.Motor_GetStatus(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'GetSysInfo'):
                _devsys = gb_devsysNo
                _mno = _currentMNo
                _rt = dc.Motor_GetSysInfo(mno=_mno,par='full',mf=_devsys)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif((command == 'GetSysInfo') and (len(parameters)== 1)):
                _devsys = gb_devsysNo
                _mno = _currentMNo
                _ln = parameters[0]
                _rt = dc.Motor_GetSysInfo(mno=_mno,par=_ln,mf=_devsys)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif(message == 'GetValue'):
                _mno = _currentMNo
                _md = gb_MotorPositionFMT[int(_mno)]
                _rt = dc.Motor_GetValue(_mno,_md)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'GetValue') and (len(parameters)== 1)):
                _mno = _currentMNo
                _md = parameters[0]
                _rt = dc.Motor_GetValue(_mno,_md)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'HomePositionCorrectModeSelect') and (len(parameters)== 1)):
                _mno = _currentMNo
                _ln = parameters[0]
                _rt = dc.Motor_HomePositionCorrectModeSelect(_mno,_ln)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif(message == 'IsBusy'):
                _mno = _currentMNo
                _rt = dc.sc_isbusy(_mno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif((command == 'Preset') and (len(parameters)== 1)):
                _mno = _currentMNo
                _sv = parameters[0]
                _target = 'P'
                _rt = dc.sc_setpreset(_mno,_target,_sv)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif(message == 'ScanHome'):
                _mno = _currentMNo
                _mnoi = int(_mno)
                _accmode = defaccmode[_mnoi]
                _syncmode = '0'
                _sptblno = defspdtbln[_mnoi]
                _orgmode = deforgmode[_mnoi]
                _rt = dc.Motor_ScanHome(_mno,_accmode,_syncmode,_sptblno,_orgmode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'ScanHome') and (len(parameters)== 4)):
                _mno = _currentMNo
                _accmode = parameters[1]
                _syncmode = parameters[2]
                _sptblno = parameters[3]
                _orgmode = parameters[0]
                _rt = dc.Motor_ScanHome(_mno,_accmode,_syncmode,_sptblno,_orgmode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'SetLink') and (len(parameters)== 2)):
                _mno = _currentMNo
                _slavm1 = parameters[0]
                _dratio1 = parameters[1]
                _rt = dc.Motor_SetLink(_mno,_slavm1, _dratio1, None,None)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'SetLink') and (len(parameters)== 4)):
                _mno = _currentMNo
                _slavm1 = parameters[0]
                _dratio1 = parameters[1]
                _slavm2 = parameters[2]
                _dratio2 = parameters[3]
                _rt = dc.Motor_SetLink(_mno,_slavm1, _dratio1, _slavm2, _dratio2)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'SetOffset') and (len(parameters)== 1)):
                _mno = _currentMNo
                _setvalue = parameters[0]
                _rt = dc.Motor_SetOffset(_mno,_setvalue)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'SetSpeedTblInfo') and (len(parameters)== 5)):
                _mno = _currentMNo
                _sptblno = parameters[0]
                _stspd = parameters[1]
                _mxspd = parameters[2]
                _acctime = parameters[3]
                _dctime = parameters[4]
                _rt = dc.Motor_SetSpeedTblInfo(_mno,_sptblno,_stspd,_mxspd,_acctime,_dctime)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'SetSysTblInfoASI') and (len(parameters)== 11)):
                _mno = _currentMNo
                _stspd = parameters[0]
                _mxspd = parameters[1]
                _acctime = parameters[2]
                _dctime = parameters[3]
                _oposi = parameters[4]
                _prsc = parameters[5]
                _bclcor = parameters[6]
                _pdenomi = parameters[7]
                _pmole = parameters[8]
                _pcary = parameters[9]
                _lmspmode = parameters[10]
                _rt = dc.Motor_SetSysTblInfoASI(_mno,_stspd,_mxspd,_acctime,_dctime,_oposi,_prsc,_bclcor,_pdenomi,_pmole,_pcary,_lmspmode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt

            elif((command == 'SetValue') and (len(parameters)== 6)):
                _mno = _currentMNo
                _tposi = parameters[0]
                _accmode = parameters[1]
                _syncmode = parameters[2]
                _sptblno = parameters[3]
                _bclcor = parameters[4]
                _enccor = parameters[5]
                _rt = dc.Motor_SetValue(_mno,_tposi,_accmode,_syncmode,_sptblno,_bclcor,_enccor)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'SetValue') and (len(parameters)== 1)):
                _mno = _currentMNo
                _tposi = parameters[0]
                _mnoi = int(_mno)
                _accmode = defaccmode[_mnoi]
                _syncmode = '0'
                _sptblno = defspdtbln[_mnoi]
                _bclcor = defbaclmode[_mnoi]
                _enccor = defenccormode[_mnoi]
                _rt = dc.Motor_SetValue(_mno,_tposi,_accmode,_syncmode,_sptblno,_bclcor,_enccor)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'SetValueREL') and (len(parameters)== 6)):
                _mno = _currentMNo
                _trposi = parameters[0]
                _accmode = parameters[1]
                _syncmode = parameters[2]
                _sptblno = parameters[3]
                _bclcor = parameters[4]
                _enccor = parameters[5]
                _rt = dc.Motor_SetValueREL(_mno,_trposi,_accmode,_syncmode,_sptblno,_bclcor,_enccor)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'SetValueREL') and (len(parameters)== 1)):
                _mno = _currentMNo
                _trposi = parameters[0]
                _mnoi = int(_mno)
                _accmode = defaccmode[_mnoi]
                _syncmode = '0'
                _sptblno = defspdtbln[_mnoi]
                _bclcor = defbaclmode[_mnoi]
                _enccor = defenccormode[_mnoi]
                _rt = dc.Motor_SetValueREL(_mno,_trposi,_accmode,_syncmode,_sptblno,_bclcor,_enccor)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'SpeedTblNoSelect') and (len(parameters)== 1)):
                _mno = _currentMNo
                _sptbno = parameters[0]
                _rt = dc.Motor_SpeedTblNoSelect(_mno,_sptbno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif(message == 'Stop'):
                _mno = _currentMNo
                _rt = dc.sc_Stop(_mno,'0')
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'StopEmergency'):
                _mno = _currentMNo
                _rt = dc.sc_Stop(_mno,'1')
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)


##################                
            else:
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad command or parameters.'
######################################################################
##   Encoder handler process  
######################################################################
        elif(_category == 'Encoder'):

            if( _currentencoder not in encoderlist):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + 'Er: The name of a encoder that does not exist. '
                _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
                rt=st.send(destsendstr)
                return
            else:
                for v in range(4):
                    if(_currentencoder == encoderlist[v]):
                        _currentENo = str(v)
                        _cmck = v
                        break
                if (_cmck == 'bad'):
                    destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' ' + 'Er: The encodernumber does not exist. '
                    _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
                    rt=st.send(destsendstr)
                    return
###
            if(message.startswith('@')):
                return
            elif(message.startswith('_')):
                return
            elif(message == 'help'):
                clist1=sorted(dc.get_commandlist(_category))
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + ' '.join(clist1)
            elif(command == 'help' and len(parameters) == 1):
                _prm=parameters[0]
                _rt = dc.is_commanddefined(_category,_prm)
                if(_rt is None):
                    rt='Er: Command not found'
                else:
                    rt=dc.get_commandhelp(_rt,_prm)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(rt)
            elif(command == 'Usage' and len(parameters) == 1):
                _prm=parameters[0]
                _rt = dc.is_commanddefined(_category,_prm)
                if(_rt is None):
                    rt='Er: Command not found'
                else:
                    rt=dc.get_commandusage(_rt,_prm)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(rt)
###
            elif(message == 'GetAxisNumber'):
                _eno = _currentENo
                _rt = dc.Encoder_GetAxisNumber(_eno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif(message == 'GetValue'):
                _eno = _currentENo
                _mode = gb_EncoderPositionFMT[int(_eno)]
                _rt = dc.Encoder_GetValue(_eno,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif((command == 'GetValue') and (len(parameters)== 1)):
                _eno = _currentENo
                _mode = parameters[0]
                _rt = dc.Encoder_GetValue(_eno,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'Preset') and (len(parameters)== 1)):
                _eno = _currentENo
                _setvalue = parameters[0]
                _rt = dc.Encoder_Preset(_eno,_setvalue)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
####
            elif(message == 'GetEncoderInfo'):
                _eno = _currentENo
                _tmpc = command + ' '
                _rt = dc.Encoder_GetInfo(_eno)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'SetEncoderInfo') and (len(parameters)== 5)):
                _eno = _currentENo
                _tmpc = command + ' '
                _setinfo = message.lstrip(_tmpc)
                _ct = 'R'
                _rt = dc.Encoder_SetInfo(_eno,_setinfo,_ct)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif((command == 'SetEncoderInfo') and (len(parameters)== 8)):
                _eno = _currentENo
                _tmpc = command + ' '
                _setinfo = message.lstrip(_tmpc)
                _ct = 'F'
                _rt = dc.Encoder_SetInfo(_eno,_setinfo,_ct)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
##################                
            else:
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad command or parameters.'
######################################################################
##   Control handler process  
######################################################################
        elif(_category == 'Controller'):
            if(message.startswith('@')):
                return
            elif(message.startswith('_')):
                return
            elif(message == 'GetVersion'):
                rt = gb_ScriptName + ' Ver.'+__version__+', '+__date__+', '+__author__
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' '+rt
            elif(message == 'getversionno'):
                rt = __version__
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Ver.'+rt
            elif(message == 'hello'):
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Nice to meet you.'
            elif(message == 'help'):
                clist1=sorted(dc.get_commandlist(_category))
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + ' '.join(clist1)
            elif(command == 'help' and len(parameters) == 1):
                _par=parameters[0]
                _rt = dc.is_commanddefined(_category,_par)
                if(_rt is None):
                    rt='Er: Command not found'
                else:
                    rt=dc.get_commandhelp(_rt,_par)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + rt
            elif(command == 'Usage' and len(parameters) == 1):
                _prm=parameters[0]
                _rt = dc.is_commanddefined(_category,_prm)
                if(_rt is None):
                    rt='Er: Command not found'
                else:
                    rt=dc.get_commandusage(_rt,_prm)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(rt)   # str() 20220913
###
            elif(message == 'flushdata'):
                _rt = dc.Ctl_flushdata()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'flushdatatome'):
                _from = gb_cliant
                _rt = dc.Ctl_flushdata(_from)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'GetMachineName'):
                _rt = gb_DEVICE
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'GetControllerName'):
                _rt = gb_DEVICE
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'GetDeviceName'):
                _rt = gb_DEVICE
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'GetEncoderList'):
                _rt = encodername
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif((command == 'GetEncoderName') and (len(parameters)== 1)):
                _ln = int(parameters[0]) -1
                _rt = dc.mn2ename(str(_ln))
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif(message == 'GetFunction'):
                _rt = gb_Flg_remote
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'GetMotorList'):
                _rt = motorname
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif((command == 'GetMotorName') and (len(parameters)== 1)):
                _ln = int(parameters[0]) - 1
                _rt = dc.mn2mname(str(_ln))
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif(message == 'GetRomVersion'):
                _rt = _deviceversion
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif((command == 'SetFunction') and (len(parameters)== 1)):
                _ln = parameters[0]
                if( _ln == '1'):
                    _rt = 'Ok:'
                elif(_ln == '0'):
                    _rt = ' Sorry, this device supports remote(=1) only.'
                else:
                    _rt = 'Er: Bad Parameter.'
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif(message == 'Standby'):
                _mode = '1'
                _rt = dc.Ctl_Standby(_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif((command == 'Standby') and (len(parameters)== 1)):
                _mode = parameters[0]
                _rt = dc.Ctl_Standby(_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + _rt
            elif(message == 'Stop'):
                _mn = '-1'
                _mode = '0'
                _rt = dc.sc_Stop(_mn,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'StopEmergency'):
                _mn = '-1'
                _mode = '1'
                _rt = dc.sc_Stop(_mn,_mode)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'SyncRun'):
#                _mnox = _currentMNox
                _rt = dc.Ctl_SyncRun()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(command == 'SendRawCommand' and parameter != ''):
                if( gb_SRawC == False):
                    _rt = 'Er: SendRawCommand is a disabled setting.'
                else:
                    _fnc = 'SendRawCommand'
                    _cmd = parameter
                    _cond = parameter.split('/')[0]
                    _rt = dc.sc_sendcmd(_fnc,_cmd,_cond)
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + '; ' + str(_rt)
            elif(message == 'terminate'):
                st.terminateMainloop()
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Ok:'
            else:
                destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad command or parameters.'
################################################################################################################################
        else:
            destsendstr = allmess.nodeto + '>' + allmess.nodefrom+' @' + message + ' Er: Bad command or parameters.'
################################################################################################################################
        if(destsendstr != ''):
            _outputlog(INFO,'STARS Send[' +st.nodename + "]:"+destsendstr)
            rt=st.send(destsendstr)
            if(rt==False):
                st.terminateMainloop()
        return

    ####################################
    #      Device exclusive control    #
    ####################################
#    def isbusyflgCtl(ctld):
#        _fctl = 'System _ChangedCtlIsBusy ' + ctld
#        st.send(_fctl)
#        return

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
    gb_PCHK=args.paracheckoff
    
    gb_SRawC = args.sendrawcommand
    gb_LimitStatusEnable = args.flg_limitstatus_enable

    if(gb_Debug==True):
        sys.stdout.write(str(args)+'\n')

    starsNodeName = optIO.get(args.StarsNodeName,None)
    if(starsNodeName is None):
        _rt = 'Stars node name input required.'
        sys.stdout.write(_rt +'\n')
        exit(1)
    elif((starsNodeName == 'sc400') or (starsNodeName == 'sc200')):
            supportdevice = starsNodeName
    else:
        _rt = 'Sorry, the input model is not supported. Please check the model.'
        sys.stdout.write(_rt +'\n')
        exit(1)

    configF = optIO.get(args.Config,None)
    if(configF is not None):
        configFileName = configF




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
    encodername     = cfgIO.get(starsNodeName, 'EncoderName', encodername)

    # Fix optional parameters
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

    gb_MotorNameList = motorname.split(' ')
    gb_EncoderNameList = encodername.split(' ')

    if(gb_Debug==True):
        sys.stdout.write("starsNodeName#"+str(starsNodeName)+"#"+'\n')
        sys.stdout.write("starsServerHost#"+str(starsServerHost)+"#"+'\n')
        sys.stdout.write("starsServerPort#"+str(starsServerPort)+"#"+'\n')
        sys.stdout.write("deviceHost#"+str(deviceHost)+"#"+'\n')
        sys.stdout.write("devicePort#"+str(devicePort)+"#"+'\n')

    ##################################################################
    # Main process: Start
    ##################################################################

    #Create device instance with devserver:devport 
    dc=PyStarsDevice_sc400(deviceHost, devicePort)
    gb_DeviceInstance=dc

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
    _devErr = 'Er:'
    _rt = 'Ok:'
    _cmd = 'IDN'
    _cdv = dc.device_act(_cmd)


    _verD = _cdv.split('\t')
##

###
    if(('C' == _verD[0]) and ('IDN0' == _verD[1])):
        _stsmatch2 = re.fullmatch('2\d\d',_verD[2])
        _stsmatch4 = re.fullmatch('4\d\d',_verD[2])
        _stsmatch8 = re.fullmatch('8\d\d',_verD[2])

        if(_stsmatch2 is not None):
            gb_devtype = 'sc200'
            gb_NumberOfAxis = 2
            gb_NumberOfMotor = 0
        elif(_stsmatch4 is not None):
            gb_devtype = 'sc400'
            gb_NumberOfAxis = 4
            gb_NumberOfMotor = 3
        elif(_stsmatch8 is not None):
            gb_devtype = 'sc800'
            gb_NumberOfAxis = 8
            gb_NumberOfMotor = 7
        else:
            _rt = ' ----> ' + _devErr + ' The device is not supported.'
    else:
        _rt = ' ----> ' + _devErr + ' Return data is not version data.'

    if('0' == _verD[2][1]):
        gb_devsysNo = '47'
    if('Er:' in _rt):
        sys.stdout.write(_rt + '\n')
        exit(1) 

    gb_DEVICE = 'SC' + _verD[2]

    if(len(_verD) == 4):
        _deviceversion = _verD[3]
    else:
        _rt = ' ----> ' + _devErr + ' Invalid version data.'
    if('Er:' in _rt):
        sys.stdout.write(_rt + '\n')
        exit(1)
#------------------------------------------
    if( gb_devtype != supportdevice):
        sys.stdout.write( ' ----> ' + 'Mismatch between NodeName and the connected device.' + '\n')
        exit(1)

# device information setting
    _axisni = gb_NumberOfAxis
    _mtname = {}
    _ecname = {}
    _flgLM = {}
    _defBACL = {}
    _defAccM = {}
    _defECM = {}
    _defOrgM = {}

    for v in range(_axisni):
        _mtname[gb_MotorNameList[v]] = str(v)
        _ecname[gb_EncoderNameList[v]] = str(v)
        _flgLM[v] = '0'
        _rsts0 = dc.sc_getsysinfo(v,8,8,1)
        if('NA' in _rsts0):         # NA --> No Answer
            sys.stdout.write( ' ----> ' + 'No response regarding system information.' + '\n')
            exit(1)
        else:
            _defBACL[v] = _rsts0
        _rsts1 = dc.sc_getsysinfo(v,22,22,1)
        if('NA' in _rsts1):         # NA --> No Answer
            sys.stdout.write( ' ----> ' + 'No response regarding system information.' + '\n')
            exit(1)
        else:
            _defAccM[v] = _rsts1
        _rsts2 = dc.sc_getsysinfo(v,29,29,1)
        if('NA' in _rsts2):         # NA --> No Answer
            sys.stdout.write( ' ----> ' + 'No response regarding system information.' + '\n')
            exit(1)
        else:
            _defECM[v] = _rsts2
        _rsts3 = dc.sc_getsysinfo(v,9,9,1)
        if('NA' in _rsts3):         # NA --> No Answer
            sys.stdout.write( ' ----> ' + 'No response regarding system information.' + '\n')
            exit(1)
        else:
            _defOrgM[v] = _rsts3


        #####
    gb_Motor2Ch = _mtname           # 2=to
    gb_Encoder2Ch = _ecname         # 2=to

    gb_Flg_LimitStatus = _flgLM
    gb_DefaultBacklachMode = _defBACL
    gb_DefaultAccMode = _defAccM
    gb_DefaultEncoderCorrectMode = _defECM
    gb_DefaultOrgMode = _defOrgM
        #####
    dc.sc_reset_syncrun()
    gb_Interval_Time = INTERVAL_STOP

    gb_devicename = starsNodeName
    dc.Ctl_flushdata()


    print('\n' + '  <<<<<< main loop start >>>>>>  ' + '\n')       # Start accepting commands


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
