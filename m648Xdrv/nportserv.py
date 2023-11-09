#! /usr/bin/python3

"""
  nportserv python program
    Description: Simple socket library.
    History:
       0.2     1st version     2016.11.17    Yasuko Nagatani
"""

# Define: program info
__author__ = 'Yasuko Nagatani'
__version__ = '0.2'
__date__ = '2016-11-17'
__license__ = 'KEK'

import sys
import socket
import select

class nportserv():
    """Class nportserv
         Default read timeout(sec) : DEFAULT_TIMEOUT(=3)
         Default delimiter string  : DEFAULT_DELIMITER(=\n)
         Use <instance>.getlasterrortext() to get error information text.
    """
    TCP_BUFFER_SIZE   = 4096
    DEFAULT_TIMEOUT   = 3
#    DEFAULT_DELIMITER = "\n"
#    DEFAULT_DELIMITER = "\r\n"
    DEFAULT_DELIMITER = "\r"

    def __init__(self, srvhost, srvport):
        """Initialize the nportserv with the arguments of server host and port.
        """
        self.srvhost    = srvhost
        self.srvport    = srvport
        self.readable   = None
        self.readbuffer = ''
        self.s          = None
        self.debug      = False
        self.error      = 'Just initialized.'
        self.connectiontimeout = 3
        self.settimeout(None)
        self.setrecvdelimiter(None)
        self.setsenddelimiter(None)

    #--------------------------------------------------------------------------
    def setdebug(self, b):
        """
             Set true to the argument b, print debug info to stdout.
        """
        if(b == True):
            self.debug = b
        else:
            self.debug = False
        return(True)

    #--------------------------------------------------------------------------
    def gettimeout(self):
        """
           Return the default read timeout seconds.
        """
        return(self.recvtimeout)

    def settimeout(self, timeout=None):
        """Set the default read timeout seconds.
               if set None, reset to the default value DEFAULT_TIMEOUT.
           Return False if invalid arguments detected.
        """
        try:
            if(timeout is None):
                timeout=nportserv.DEFAULT_TIMEOUT
            elif(timeout<0):
                self.error="timeout value %s error. [timeout>=0]" %(timeout)
                return(False)
            self.recvtimeout=timeout
        except Exception as e:
            self._debugprint("%s\n" %e)
            self.error="timeout value %s error. [%s]" %(timeout, sys.exc_info()[0])
            return(False)
        return(True)

    #--------------------------------------------------------------------------
    def getrecvdelimiter(self):
        """Return the default read delimiter string.
        """
        return(self.recvdelimiter)

    def setrecvdelimiter(self, delimiter=None):
        """Set default read delimiter string.
               if set '' as delimiter, it acts like direct read.
                 or set None, reset to the default value DEFAULT_DELIMITER.
           Return False if invalid arguments detected.
        """
        if(isinstance(delimiter, str)):
            self.recvdelimiter = delimiter
        elif(delimiter is None):
            self.recvdelimiter = nportserv.DEFAULT_DELIMITER
        else:
            self.error="recvdelimiter value %s error. [TypeError]" %(delimiter)
            return(False)
        return(True)
    #--------------------------------------------------------------------------
    def getsenddelimiter(self):
        """Return the default send delimiter string.
        """
        return(self.senddelimiter)

    def setsenddelimiter(self, delimiter=None):
        """Set default delimiter string which automatically added to send string.
               if set '' as delimiter, it acts like direct write.
                 or set None, reset to the default value DEFAULT_DELIMITER.
           Return False if invalid arguments detected.
        """
        if(isinstance(delimiter, str)):
            self.senddelimiter = delimiter
        elif(delimiter is None):
            self.senddelimiter = nportserv.DEFAULT_DELIMITER
        else:
            self.error="senddelimiter value %s error. [TypeError]" %(delimiter)
            return(False)
        return(True)
    #--------------------------------------------------------------------------
    def setdelimiter(self, delimiter=None):
        """Set both default recv and send delimiter string.
              if set '' as delimiter, it acts like direct read and write.
                 or set None, reset to the default value DEFAULT_DELIMITER.
           Return False if invalid arguments detected.
        """
        rt=self.setrecvdelimiter(delimiter)
        if(rt == False):
            return(rt)
        rt=self.setsenddelimiter(delimiter)
        return(rt)
    #--------------------------------------------------------------------------
    def printinfo(self):
        """Print the instance variables info, Just use for debug.
        """
        d=self.debug
        self.debug = True
        self._debugprint("svrhost=%s\n" %self.srvhost)
        self._debugprint("svrport=%s\n" %self.srvport)
        self._debugprint("timeout=%s\n" %self.gettimeout())
        self._debugprint("recvdelimiter=%s\n" %self.getrecvdelimiter())
        self._debugprint("senddelimiter=%s\n" %self.getsenddelimiter())
        self._debugprint("isconnected=%s\n" %self.isconnected())
        self._debugprint("readble=%s\n" %self.readable)
        self._debugprint("readbuffer=%s\n" %self.readbuffer)
        self._debugprint("error=%s\n" %self.error)
        self._debugprint("debug=%s\n" %d)
        self.debug=d

    def _debugprint(self,msg):
        if(self.debug == True):
            sys.stdout.write(msg)

    def getlasterrortext(self):
        """Return the last error string.
        """
        return(self.error)

    def gethandle(self):
        """Return socket handle, None value means no socket.
        """
        if hasattr(self,'s'):
            if(self.s is None):
                self.error='No socket for STARS.'
            return(self.s)
        self.error='No socket for STARS.'
        return(None)

    #--------------------------------------------------------------------------
    def isconnected(self):
        """Return connected or not.
             Return True if has connection.
             Return False if not has connection.
        """
        if(self.s is None):
            return(False)
        return(True)

    def connect(self, force=False):
        """Connect to server:port
             Return False for connection error.
               or else return True.
             Set True to the argument to automatically close opened connection before connect.
        """
        if(self.isconnected()):
            if(force == False):
                self.error="Already connected."
                return(force)
            self.disconnect(force)

        self.readbuffer = ''
        self.error      = ''
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.settimeout(self.connectiontimeout)
            self.s.connect((self.srvhost, self.srvport))
            self.readable = set([self.s])
        except socket.timeout:
            self.error="Connect error to %s:%s. [Timeout]" %(self.srvhost, self.srvport)
            self.s        = None
            self.readable = None
            return(False)
        except Exception as e:
            self._debugprint("%s\n" %e)
            self.error="Connect error to %s:%s. [%s]" %(self.srvhost, self.srvport, sys.exc_info()[0])
            self.s        = None
            self.readable = None
            return(False)
        self._debugprint("[connect]#True\n")
        return(True)

    def disconnect(self, force=True):
        """Disconnect from server:port
             If force is True, always return True.
               or else return False for disconnect error.
        """
        if(self.isconnected() == False):
            self.readbuffer = ''
            self.s        = None
            self.readable = None
            if(force == False):
                self.error="No socket."
            return(force)

        try:
            self.s.close()
            force = True
        except Exception as e:
            self._debugprint("%s\n" %e)
            self.error="Disconnect error.[message=%s]" %sys.exc_info()[0]
        self.readbuffer = ''
        self.s        = None
        self.readable = None
        self._debugprint("[disconnect]#%s\n" %(str(force)))
        return(force)

    #--------------------------------------------------------------------------
    def send(self, smsg, delimiter=None):
        """Send message
             Return False for send error,
               or else return True.
             Set the arguments - delimieter if change temporarily the default value.
        """
        if(self.isconnected() == False):
            self.error = 'No connection'
            self._debugprint("[send]#%s#->\n" %(smsg,self.error))
            return(False)

        if(isinstance(delimiter, str)):
            delimiter = ''
        elif(delimiter is None):
            delimiter = self.senddelimiter
        else:
            bk_delimiter=self.senddelimiter
            rt = self.setsenddelimiter(delimiter)
            self.senddelimiter=bk_delimiter
            if(rt == False):
                return('')

        self._debugprint("[send]#%s#\n" %(smsg+delimiter))
        
        try:
            self.s.sendall((smsg+delimiter).encode())
        except socket.error as e:
            self.error="Send error.[sendstr=%s, delimiter=%s, message=%s]" %(smsg, delimiter, e)
            self._debugprint("[send]#Error->%s#\n" %self.error)
            self.error="Send error.[sendstr=%s, delimiter=%s, message=%s]" %(smsg, delimiter, sys.exc_info()[0])
            return(False)
        except Exception as e:
            self.error="Send error.[sendstr=%s, delimiter=%s, message=%s]" %(smsg, delimiter, e)
            self._debugprint("[send]#Error->%s#\n" %self.error)
            self.error="Send error.[sendstr=%s, delimiter=%s, message=%s]" %(smsg, delimiter, sys.exc_info()[0])
            return(False)
        return(True)

    #--------------------------------------------------------------------------
    def _process_message(self, msg, delimiter):
        self.readbuffer += msg
        if(delimiter == ''):
            rtmess = self.readbuffer
            self.readbuffer = ''
            return rtmess
        dlen = len(delimiter)
        dpw = self.readbuffer.find(delimiter)
        if dpw < 0:
            return('')
        dp = dpw
        clist=list(self.readbuffer)
        #for i in range(dp):
            #print("C"+str(ord(clist[i])))
        rtmess = self.readbuffer[:dp]
        #print(dp)
        #print(len(rtmess))
        self.readbuffer = self.readbuffer[dp+len(delimiter):]
        return rtmess

    def receive(self, timeout = None, delimiter=None, exceptionret = None):
        """Receieve message
             Return argument exceptionret value, default None, for fatal error,
              or return '' for timeout,
              or else return received data.
             Set the arguments - timeout, delimieter if change temporarily the default value.
        """
        if(self.isconnected() == False):
            self.error = 'No connection'
            self._debugprint("[receive]#%s#->\n" %(self.error))
            return(exceptionret)

        if(timeout is None):
            timeout=self.recvtimeout
        else:
            bk_timeout=self.recvtimeout
            rt = self.settimeout(timeout)
            self.recvtimeout=bk_timeout
            if(rt == False):
                return(exceptionret)

        if(isinstance(delimiter, str)):
            delimiter = ''
        elif(delimiter is None):
            delimiter = self.recvdelimiter
        else:
            bk_delimiter=self.recvdelimiter
            rt = self.setrecvdelimiter(delimiter)
            self.recvdelimiter=bk_delimiter
            if(rt == False):
                return(exceptionret)

        readfds = self.readable;
        rmsg = ''

        while True:
            #Just print
            if(self.readbuffer != ""):
                self._debugprint("[receive#rbuf]#%s#\n" %self.readbuffer)

            #Check readbuffer
            rtmsg = self._process_message(rmsg, delimiter)
            if rtmsg != '':
                self._debugprint("[recv]#%s#\n" %rtmsg)
                return(rtmsg)

            #Check read socket
            #self._debugprint("timeout"+str(timeout))
            try:
                rready, wready, xready = select.select(readfds, [], [], timeout)
                if(len(rready) == 0):
                    self.error = 'Timeout'
                    self._debugprint("[recv] <<point-A>> #Warning->%s#\n" %self.error)
                    return('');
            except Exception as e:
                self.error="Recv select error.[%s]" %e
                self._debugprint("[recv]#Error->%s#\n" %self.error)         # temp for making sure 20220711
                self.error="Recv select error.[%s]" %sys.exc_info()[0]
                return(exceptionret)

            #Read socket
            rmsg = ''
            try:
                self.s.settimeout(self.DEFAULT_TIMEOUT)
                rmsg = self.s.recv(self.TCP_BUFFER_SIZE).decode()
            except Exception as e:
                self.error="Recv error.[%s]" %e
                self._debugprint("[recv]#Error->%s#\n" %self.error)
                self.error="Recv error.[%s]" %sys.exc_info()[0]
                return(None)
            if(len(rmsg) == 0):
                self.error = 'Connection closed from remote'
                self._debugprint("[recv] <<point-B>> #Warning->%s#\n" %self.error)
                return(exceptionret)
        return(exceptionret)
