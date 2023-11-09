#Configuration of m2xxxdrv Client.

if(
$::NodeName eq 'm2701drvA2'
){###############################################################################

#STARS server
$::Server = 'localhost';
#$::Server = '192.168.11.100';

## For NPORT interface
$::NPORT_HOST  = '192.168.1.110'; #NPort host name.
$::NPORT_PORT  = 1394;             #NPort port number.

$::DESTINATION{'ch01'} = "101";
$::DESTINATION{'ch02'} = "102";
$::DESTINATION{'ch03'} = "103";
$::DESTINATION{'ch04'} = "104";
$::DESTINATION{'ch05'} = "105";
$::ALIAS{'all'} = "ch01,ch02,ch03,ch04,ch05";


$::NPLC_MAX = 50;

$::RegFile = 'reg.txt';		#Registry fileM

$::DMMTYPE_M2000 = 0;

#functions----------------------------------------
%::dmm_func_functions = (
'ACI',   'CURR:AC',
'DCI',   'CURR:DC',
'ACV',   'VOLT:AC',
'DCV',   'VOLT:DC',
'2OHM',  'RES',
'4OHM',  'FRES',
'FREQ',  'FREQ',
'TEMP',  'TEMP'
);

%::dmm_NPLC_functions = (
'ACI',   ':CURR:AC:NPLC',
'DCI',   ':CURR:DC:NPLC',
'ACV',   ':VOLT:AC:NPLC',
'DCV',   ':VOLT:DC:NPLC',
'2OHM',  ':RES:NPLC',
'4OHM',  ':FRES:NPLC',
'TEMP',  ':TEMP:NPLC',
);

%::dmm_range_functions = (
'ACI',   ':CURR:AC:Range',
'DCI',   ':CURR:DC:Range',
'ACV',   ':VOLT:AC:Range',
'DCV',   ':VOLT:DC:Range',
'2OHM',  ':RES:Range',
'4OHM',  ':FRES:Range',
'FREQ',  ':FREQ:THR:VOLT:Range',
);

%::dmm_range_values = (
$::dmm_range_functions{'ACI'},   ',1,3,AUTO,',
$::dmm_range_functions{'DCI'},   ',0.01,0.1,1,3,AUTO,',
$::dmm_range_functions{'ACV'},   ',0.1,1,10,100,750,AUTO,',
$::dmm_range_functions{'DCV'},   ',0.1,1,10,100,1000,AUTO,',
$::dmm_range_functions{'2OHM'},  ',0.1,1,10,100,1000,10000,100000,AUTO,',
$::dmm_range_functions{'4OHM'},  ',0.1,1,10,100,1000,10000,100000,AUTO,',
$::dmm_range_functions{'FREQ'},  ',0.1,1,10,100,1000,'
);

%::dmm_unit_functions = (
'ACV',   ':UNIT:VOLT:AC',
'DCV',   ':UNIT:VOLT:DC',
'TEMP',  ':UNIT:TEMP',
);

%::dmm_unit_values = (
$::dmm_unit_functions{'ACV'},   ',V,DB,DBM,',
$::dmm_unit_functions{'DCV'},   ',V,DB,DBM,',
$::dmm_unit_functions{'TEMP'},  ',C,CEL,F,FAR,K,'
);

################################################################################

}else{
	die "Bad node name.";
}
1;
