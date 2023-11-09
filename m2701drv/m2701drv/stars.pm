package stars;

#STARS interface module
#2004-03-31 Ver.1.3 Takashi Kosuge
#Org. 2001-10-03


use strict;
use IO::Socket;
use Symbol;
use IO::Select;

%stars::cbhandler=();
%stars::cbmode=();
%stars::cbbuf=();
$stars::cbobj='';

#Usage: $object->removecallback(filehandle);
sub removecallback{
	my $this=shift;
	my $fh=shift;
	my $fhbuf;
	my $lp;
	my $hcount=@stars::cbhandle;
	delete($stars::cbhandler{$fh});
	delete($stars::cbmode{$fh});
	delete($stars::cbbuf{$fh});
	$stars::cbobj->remove($fh);
}

#Usage: $object->addcallback(subroutine, [filehandle], [mode]);
sub addcallback{
	my $this=shift;
	my $handler=shift;
	my $fh=shift;
	my $mode=shift;

	unless($fh){$fh=$this->{fh};}
	unless($mode){$mode='Stars';}
	unless($mode eq 'Direct' or $mode eq 'Lf' or $mode eq 'Stars' or $mode eq 'Detect'){
		$mode='Direct';
	}
	$stars::cbhandler{$fh}=$handler;
	$stars::cbmode{$fh}=$mode;
	$stars::cbbuf{$fh}='';

	unless($stars::cbobj){$stars::cbobj=IO::Select->new;}
	$stars::cbobj->add($fh);
}

#Usage: stars->Mainloop([\&sub, timeout|\timeout]);
#Changed, timeout can be reference. 2002-02-22
sub Mainloop{
	my $dummy=shift;
	my $handler=shift;
	my $timeoutval=shift;
	my $timeout;
	my $fintimeout;
	my $ready;

	my $s;
	my $buf;
	if(ref($timeoutval)){
		$timeout=$timeoutval;
	}elsif($timeoutval){
		$timeout=\$timeoutval;
	}else{
		$timeout = \-1;
	}

	while(1){
		if($$timeout < 0){
			$fintimeout = undef;
		}else{
			$fintimeout = $$timeout/1000;
		}
		unless(($ready)=IO::Select->select($stars::cbobj,undef,undef,$fintimeout)){
			if($handler ne ''){$handler->();}
			next;
		}
		foreach $s (@$ready){
			if($stars::cbmode{$s} eq 'Detect'){
				$stars::cbhandler{$s}->();
			}elsif(sysread($s, $buf, 512)){
				if($stars::cbmode{$s} eq 'Direct'){
					$stars::cbhandler{$s}->("$buf");
					next;
				}
				$stars::cbbuf{$s} .= $buf;
				while($stars::cbbuf{$s} =~ s/([^\r\n]*)\r*\n//){
					$buf=$1;
					if($stars::cbmode{$s} eq 'Stars'){
unless($buf =~ s/^([a-zA-Z_0-9.\-]+)>([a-zA-Z_0-9.\-]+)\s*//){next;}
						$stars::cbhandler{$s}->("$1","$2","$buf");
					}else{
						$stars::cbhandler{$s}->("$buf");
					}
				}
			}else{
				delete $stars::cbhandler{$s};
				delete $stars::cbmode{$s};
				delete $stars::cbbuf{$s};
				$stars::cbobj->remove($s);
#				return(undef);
				return($s);
			}
		}
	}
}

#Usage: $object = stars->new(nodename, [serverhost], [serverport], [keyfile]);
sub new{
	my $class = shift;
	my ($nodename,$adr,$port,$keyfile)=@_;
	my $fh;
	my $rt;

	unless($adr){$adr='localhost';}
	unless($port){$port=6057;}
	unless($keyfile){$keyfile = "$nodename.key";}
	unless($fh = new IO::Socket::INET (PeerAddr => "$adr"
										,PeerPort => $port
										,Proto    => 'tcp')){return(undef);}
	select($fh);$|=1;select(STDOUT);
	binmode($fh);

##---get keynumber from file
	my $keynumber;
	my $keyval='';
	my $kcount=0;
	my $lp;
	my $hd = gensym();
	$keynumber=<$fh>;chomp($keynumber);$keynumber=~s/\r//;

	unless(open($hd, "$keyfile")){
		close($fh); return(undef);
	}
	while(<$hd>){$kcount++;}
	unless($kcount){close($hd); close($fh); return(undef);}

	$kcount = $keynumber % $kcount;
	seek($hd, 0, 0);
	for($lp=0; $lp < $kcount; $lp++){$_=<$hd>;}
	$_=<$hd>;
	chomp;s/\r//;
	close($hd);
#---------------------
	print $fh "$nodename $_\n";
	$rt=<$fh>;chop($rt);$rt=~s/\r//;
	unless($rt =~ /Ok:/){
#		print $fh "quit\n";
		close($fh);
		return(undef);
	}
	my $this = {};
	bless $this, $class;
	$this->{fh}=$fh;
	$this->{readable} = IO::Select->new();
	$this->{readable}->add($fh);
	$this->{timeout} = 10;
	return($this);
}

#Usage: $fh = $object->gethandle();
sub gethandle{
	my $this=shift;
	return($this->{fh});
}

#Usage: val/list = $object->Read();
sub Read{
	my $this=shift;
	my $timeout=shift;
	my $fh=$this->{fh};
	my $buf;
	my $readable = $this->{readable};
	my $ready;

	unless($timeout){$timeout=0.001;}
  while(1){
	if($stars::cbbuf{$fh} =~ s/([^\r\n]*)\r*\n//){
		$buf = $1;
		if(wantarray){
			unless($buf =~ s/^([a-zA-Z_0-9.\-]+)>([a-zA-Z_0-9.\-]+)\s*//){
				$::Error = "Read error";
				return(());
			}
			return("$1","$2","$buf");
		}
		return("$buf");
	}
	unless(($ready) = $readable->can_read($timeout)){
		if($timeout != 0.001){
			$::Error = "Timeout";
		}
		if(wantarray){
			return('', '', '');
		}
		return('');
	}
	unless( sysread($fh, $buf, 512) ){return(undef)};
	$stars::cbbuf{$fh} .= $buf;
  }
}

sub DESTROY{
	my $this=shift;
	my $fh = $this->{fh};
	print $fh "quit\n";
	close($fh);
}

#Usage: $object->Send(message [, termto]);
sub Send{
	my $this=shift;
	my $cmd=shift;
	my $termto = shift;

	my $fh = $this->{fh};
	if($termto){
		print $fh "$termto $cmd\n";
	}else{
		print $fh "$cmd\n";
	}
}

#Usage: val/list = $object->act(message);
sub act{
	my $this=shift;
	my $cmd=shift;

	my $buf;
	my $from;
	my $to;

	$this->Send($cmd);
	while(1){
		unless(($from,$to,$buf) = $this->Read($this->{timeout})){
			return(());
		}
		if($from eq ''){
			if(wantarray){return(());}else{return(());}
		}
		if($buf =~ /^\@/){
			last;
		}
		if(defined($stars::cbhandler{$this->{fh}})){
			$stars::cbhandler{$this->{fh}}->($from, $to, $buf);
		}
	}

	if(wantarray){
		return($from, $to, $buf);
	}
	return("$from>$to $buf");
}

#Usage: $object->Sleep(mSec);
sub Sleep{
	my $class = shift;
	my $stime=shift;
	$stime /= 1000;
	if($stime<0.001){return(undef)};
	select(undef,undef,undef,$stime);
}


1;
