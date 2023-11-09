package nportserv;

use strict;
use IO::Socket;
use IO::Select;
################################################################
# Nport Server mode Perl Module Ver. 1.0 Takashi Kosuge        #
#    2003-10-17                                                #
################################################################
use constant RCVTIMEOUT        => 3;
use constant SIOMAXLENGTH      => 1024;


# Serial port ------------------------------------------------------
sub GetSIOHandle{
	my $this = shift;
	return($this->{sport});
}

sub OutSIO{
	my $this = shift;
	my $buf  = shift;
	my $fh   = $this->{sport};
	print $fh $buf;
	return(1);
}

sub InSIO{
	my $this = shift;
	my $timeout = shift;
	unless($timeout){$timeout=RCVTIMEOUT;}

	my $buf;
	my $fh = $this->{sport};

	if($this->{spreadable}->can_read($timeout)){
		sysread($fh, $buf, SIOMAXLENGTH);
		return($buf);
	}
	return('');
}


#New and destroy this module ------------------------------------------
sub DESTROY{
	my $this=shift;
	close($this->{sport});
}
#Usage: $object = nportserv->new('host', [SerialPort]);
sub new{
	my $class  = shift;
	my $npadr = shift;
	my $sp     = shift;

	my $spfh;

	unless($npadr){$npadr = '192.168.0.230';}
	unless($sp){$sp = 4001;}

#Open serial port
	unless($spfh = new IO::Socket::INET (PeerAddr => "$npadr"
										,PeerPort => $sp
										,Proto    => 'tcp')){return(undef);}
	select($spfh);$|=1;select(STDOUT);
	binmode($spfh);

	my $this = {};
	bless $this, $class;

	$this->{sport} = $spfh;
	$this->{spreadable} = IO::Select->new();
	$this->{spreadable}->add($spfh);

	return($this);
}

1;
