function mpc = case5
%CASE5  Power flow data for modified 5 bus, 5 gen case based on PJM 5-bus system
%   Please see CASEFORMAT for details on the case file format.
%
%   Based on data from ...
%     F.Li and R.Bo, "Small Test Systems for Power System Economic Studies",
%     Proceedings of the 2010 IEEE Power & Energy Society General Meeting

%   Created by Rui Bo in 2006, modified in 2010, 2014.
%   Distributed with permission.

%   MATPOWER

%% MATPOWER Case Format : Version 2
mpc.version = '2';

%%-----  Power Flow Data  -----%%
%% system MVA base
mpc.baseMVA = 100;

%% bus data
%	bus_i	type	Pd	Qd	Gs	Bs	area	Vm	Va	baseKV	zone	Vmax	Vmin
mpc.bus = [
	1	0	0	0	0	0	1	1	0	230	1	1.1	0.9;
	2	1	100	0	0	0	1	1	0	230	1	1.1	0.9;
	3	1	100	0	0	0	1	1	0	230	1	1.1	0.9;
	4	1	100	0	0	0	1	1	0	230	1	1.1	0.9;
];

%% generator data
%	bus	Pg	Qg	Qmax	Qmin	Vg	mBase	status	Pmax	Pmin	Pc1	Pc2	Qc1min	Qc1max	Qc2min	Qc2max	ramp_agc	ramp_10	ramp_30	ramp_q	apf type cost TYPE
mpc.gen = [
	1	0	0	0	0	1	100	1	300	0	0	0	0	0	0	0	0	0	0	0	0 1;
];

%% branch data
%	fbus	tbus	r	x	b	rateA	rateB	rateC	ratio	angle	status	angmin	angmax
mpc.branch = [
	1	2	0.02	0.04	0.01	100	100	100	0	0	1	-360	360;
	1	2	0.02	0.04	0.01	100	100	100	0	0	1	-360	360;
	1	3	0.02	0.04	0.01	100	100	100	0	0	1	-360	360;
	2	3	0.02	0.04	0.01	100	100	100	0	0	1	-360	360;
];

%% expansion branch data
%	fbus	tbus	r	x	b	rateA	rateB	rateC	ratio	angle	status	angmin	angmax nlines invTcost
mpc.xbranch = [
	1	2	0.02	0.04	0.01	100	100	100	0	0	1	-360	360  3	1e6;
	1	3	0.02	0.04	0.01	100	100	100	0	0	1	-360	360  3	1e6;
	2	3	0.02	0.04	0.01	100	100	100	0	0	1	-360	360  3	1e6;
	3	4	0.02	0.04	0.01	100	100	100	0	0	1	-360	360  3	1e6;
];

%%-----  OPF Data  -----%%
%% generator cost data
%type    cinv    cope  carbon    ramp    serie
%       ($/kW) ($/MWh)(ton/MWh) (%cap)
mpc.gencost = [
	1	3000      36    0.92      45       -1;  %  coal 
	2	3000      28       0      45       -1;  %  Nuclear;
	3	3000      41    0.51      45       -1;  %  gas
	4	1150      10       0     100        1;  %  wind
];

%% Co2tax
mpc.c02tax = [
    26;
];	% Carbon tax [$/ton]