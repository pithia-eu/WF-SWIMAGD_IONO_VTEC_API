#20120821[MHP]: Main diff. of v9 regarding to v8 is adding an automatic
#option to select, on record basis, C1, instead of P1, in case this last 
#value is not available.
#
#20120731[MHP]: Main diff. of v8 regarding to v7 is fixing a bug which
#can happen in rare cases, where a receiver clock is provided in the RINEX 
#file (the number of observations is now gathered as substr).
#
#20120607[MHP]: Main diff. of v7 regarding to v6_gps_nextgps_and_galileo is
#fixing a main bug which some times generated the no detection of cycle-slip
#after, for instance, a long interval without observation.
#
#20111123[MHP]: Main diff. of v6_gps_nextgps_and_galileo regarding to v5 is 
#adding Galileo and Next-generation GPS support, among GPS support.
#20080804: Main difference of v5 regarding to v4 is the new externally
# provided option integer_phase_ambiguity_alignement which can be Y or N, and 
# which allows disconnecting this feature in order to compare ambiguities
# with external computations. 
#
#20080609: Main difference of v4 (_L1...) regarding to v3 is the optional
#relabelling of the receiver to an externally given id, quite convenient 
# option for LEOs, replacing #LEOrec name by LEOid, for instance (by default
# id=rec).
#20080327: Main difference of v3_L1L2P2P1 regarding to v3 is the substitution 
#of C1 by P1, in GPS input records.
#20080222: Main difference of v3 regarding to v2 is the fixing of an
# small bug in computation of time in seconds, referred to the first day of the
# given month, tmsec
#
# Input variables:
#setenv GTdtsecmax 931.
#setenv GTd2Limax_per_sec 0.002
BEGIN{
	blank14="              "
# Default values for the input variables:
	if(length(dtsecmax)==0)dtsecmax=931
	if(length(d2Limax0)==0)d2Limax0=0.04
	if(length(d2Limax_per_sec)==0)d2Limax_per_sec=0.002
	if(length(dBwmax)==0)dBwmax=50.
	if(length(dBewmax)==0)dBewmax=5.
	if(length(dlew_wmax)==0)dlew_wmax=0.5
        if(length(integer_phase_ambiguity_alignement)==0)integer_phase_ambiguity_alignement="y"
        
#	if(length(xsigmaBw)==0)xsigmaBw=4
#	if(length(sigmaBw0)==0)sigmaBw0=0.5
#	if(length(dBwmax)==0)dBwmax=10
	print "dtsecmax= "dtsecmax > "OBS_2_OB1.v2.log"
	print "d2Limax_per_sec= "d2Limax_per_sec > "OBS_2_OB1.v2.log"
#	print "xsigmaBw= "xsigmaBw > "OBS_2_OB1.v2.log"
#	print "sigmaBw0= "sigmaBw0 > "OBS_2_OB1.v2.log"
	print "dBwmax= "dBwmax > "OBS_2_OB1.v2.log"
	print "dBewmax= "dBewmax > "OBS_2_OB1.v2.log"

	c=299792458.d0
	f0=10.23e+6
#L1 (GPS), E1 (GALILEO)
	f1=154*f0
#L2 (GPS)
	f2=120*f0
#L5 (GPS), E5a (GALILEO)
	f5=115*f0
#E5b (GALILEO)
	f7=118*f0

	f12=f1*f1
	f22=f2*f2
	f52=f5*f5
	f72=f7*f7

	fw_gps=f1-f2
	few_gps=f2-f5
	fn_gps=f1+f2

#	fw_gal=f1-f7
	fw_gal=f1-f5
	few_gal=f7-f5
#	fn_gal=f1+f7
	fn_gal=f1+f5

#fe=f7-f5
#fen=f7+f5
#fw=f1-f2
#fm=f1-f3
#fn=f1+f2
#fmn=f1+f3

	wl1=c/f1
	wl2=c/f2
	wl5=c/f5
	wl7=c/f7

	wlw_gps=c/fw_gps
	wlew_gps=c/few_gps
	wln_gps=c/fn_gps

	wlw_gal=c/fw_gal
	wlew_gal=c/few_gal
	wln_gal=c/fn_gal

#	wle=c/fe
#	wlw=c/fw
#	wln=c/fn
#	wlen=c/fen
#        iono_threshold_w_e=wlw*f1*f2*f3/40.3/fm/2
#        iono_threshold_1_w=wl1*f12*f2/40.3/fn/2
#        iono_ew=40.3*1.e+16/f2/f3
#        iono_w=40.3*1.e+16/f1/f2
#        iono_1=-40.3*1.e+16/f1/f1
#	Bi_2_B1=-wl1**2/(wl2**2-wl1**2)
#	Bi_2_B2=-wl2**2/(wl2**2-wl1**2)
#	Bi_2_Bw=-(wl1-wl2)/(wl2**2-wl1**2)


        konobs=0
	#d2Limax_per_sec2=d2Limax_per_sec*d2Limax_per_sec
	dtsecmax2=dtsecmax*dtsecmax

	dBwmax2=dBwmax*dBwmax
	dBewmax2=dBewmax*dBewmax
	dlew_wmax2=dlew_wmax*dlew_wmax

# 
# In the beginning of the datasets, an initial cycle-slip
# must be assumed for consistency
#
	cycleslip_dtsec="T"
	cycleslip_d2Li="T"

#
# Tolerance (maximum value of PI) to select C1, instead of P1...
#
	pi_abs_max = 1e+6

	}

function nint(x,    sx){
		if(x < 0){
			sx=-1
		}
		else
		{
			sx=1
		}

		nintx=sx*int(sx*x+.5)

	}

function OBS_2_obs(line,ikm      ){
	i=84+(ikm-1)*16
	obs=substr($0,i,14)
	ib=i+14
	ias=substr($0,ib,1)	
	ic=ib+1
	isn=substr($0,ic,1)
}

function OBS_2_obs_v2(line,nm,ikm      ){
	ii0=60+nm*6
	i=ii0+(ikm-1)*16
	obs=substr($0,i,14)
	ib=i+14
	ias=substr($0,ib,1)	
	ic=ib+1
	isn=substr($0,ic,1)
}

/^OBS/{

#	print $0

#	nm=$13 
	nm = +substr($0,58,2)
#	print nm

	#print "nm="nm

#
# This version works with 4 measurements (typically GPS)
# or with 6 measurements (next GPS or Galileo)
#

#	if(nm==4 || nm==6){
	if( nm >=4 ){
#		l1=""
#		l2=""
#		c1=""
#		p2=""
#		p1=""
#		l5=""
#		l7=""
#		c5=""
#		c7=""

		l1="              "
		l2="              "
		c1="              "
		p2="              "
		p1="              "
		l5="              "
		l7="              "
		c5="              "
		c7="              "

		il1as=""
		il2as=""
		ip2as=""
		ic1as=""
		ip1as=""
		il5as=""
		il7as=""
		ic5as=""
		ic7as=""

		il1sn=""
		il2sn=""
		ip2sn=""
		ic1sn=""
		ip1sn=""
		il5sn=""
		il7sn=""
		ic5sn=""
		ic7sn=""

		li=""
		pi=""
		lw=""
		pw=""
		lc=""
		pc=""
		lew=""
		pew=""

#
# Pointer beginning and increment of index between the measurement labels in OBS
#
		i0=64
		di=6
#
		for(ikm=1;ikm<=nm;ikm++){
#			km=$(13+ikm)
			i=i0+(ikm-1)*di
			km=substr($0,i,2)

			if(km=="L1"){
#			i1=84+(ikm-1)*16
#			l1=substr($0,i1,14)
#			i1b=i1+14
#			ias1=substr($0,i1b,1)
#			i1c=i1b+1
#			isn1=substr($0,i1c,1)
#				OBS_2_obs($0,ikm    )
				OBS_2_obs_v2($0,nm,ikm    )
				l1=obs
				il1as=ias
				il1sn=isn
#			print "L1= "l1 
#			print "ias1= "ias1
#			print "isn1= "isn1
			}
			if(km=="L2"){
#				OBS_2_obs($0,ikm    )
				OBS_2_obs_v2($0,nm,ikm    )
				l2=obs
				il2as=ias
				il2sn=isn
			}

			if(km=="P2"){
				#OBS_2_obs($0,ikm    )
				OBS_2_obs_v2($0,nm,ikm    )
				p2=obs
				ip2as=ias
				ip2sn=isn
			}

			if(km=="C1"){
				OBS_2_obs_v2($0,nm,ikm    )
				c1=obs
				ic1as=ias
				ic1sn=isn
			}

			if(km=="C2"){
				OBS_2_obs_v2($0,nm,ikm    )
				c2=obs
				ic2as=ias
				ic2sn=isn
			}

			if(km=="P1"){
				OBS_2_obs_v2($0,nm,ikm    )
				p1=obs
				ip1as=ias
				ip1sn=isn
			}

			if(km=="L5"){
				OBS_2_obs_v2($0,nm,ikm    )
				l5=obs
				il5as=ias
				il5sn=isn
			}

			if(km=="L7"){
				OBS_2_obs_v2($0,nm,ikm    )
				l7=obs
				il7as=ias
				il7sn=isn
			}

			if(km=="C5"){
				OBS_2_obs_v2($0,nm,ikm    )
				c5=obs
				ic5as=ias
				ic5sn=isn
			}

			if(km=="C7"){
				OBS_2_obs_v2($0,nm,ikm    )
				c7=obs
				ic7as=ias
				ic7sn=isn
			}

		}

		#print "l1,il1as,il1sn=",l1,il1as,il1sn
		#print "l7,il7as,il7sn=",l7,il7as,il7sn
		#print "c1,ic1as,ic1sn=",c1,ic1as,ic1sn
		#print "c7,ic7as,ic7sn=",c7,ic7as,ic7sn

##		#if(length(l1)!=0 && length(l2)!=0 && length(c1)!=0 && length(p2)!=0){
#		if(length(l1)!=0 && length(l2)!=0 && length(p1)!=0 && length(p2)!=0){
#		if(l1!=blank14 && l2!=blank14 && p1!=blank14 && p2!=blank14){
		if( l1!=blank14 && l2!=blank14 && ( p1!=blank14 || c1!=blank14 ) && ( p2!=blank14 || c2!=blank14 ) ){
			gnss_system="gps"

			li=l1*wl1-l2*wl2
			#pi=p2-c1
			pi=p2-p1

			pi_abs=sqrt(pi*pi)

			if ( pi_abs > pi_abs_max ) {
				pi=p2-c1
			}

			wlw=wlw_gps
			lw=(l1-l2)*wlw_gps
			if ( pi_abs > pi_abs_max ) {
				pw=(c1*f1+p2*f2)/(f1+f2)
			}
			else
			{
				pw=(p1*f1+p2*f2)/(f1+f2)
			}

			wln=wln_gps
			lc=(l1*f1-l2*f2)*wln/(f1-f2)
			if ( pi_abs > pi_abs_max ) {
				pc=(c1*f12-p2*f22)/(f12-f22)
			}
			else
			{
				pc=(p1*f12-p2*f22)/(f12-f22)
			}

#                        if(length(c5)!=0 && length(l5)!=0){
                        if(c5!=blank14 && l5!=blank14){
                                gnss_system="next_gps"

                                wlew=wlew_gps
                                lew=(l2-l5)*wlew
                                pew=(p2*f2+c5*f5)/(f2+f5)

                        }       
			
		}
		else
		{
#			if(l1!=blank14 && l7!=blank14 && p1!=blank14 && c7!=blank14 && c5!=blank14 && l5!=blank14){
			if(l1!=blank14 && ( p1!=blank14 || c1!=blank14 ) && c5!=blank14 && l5!=blank14){

				gnss_system="gal2"

				if ( p1!=blank14 ) {
					p1eff=p1
				}
				else
				{
					p1eff=c1
				}

				#print "l1,l7,l5=",l1,l7,l5
				#print "c1,c7,c5=",c1,c7,c5

#				li=l1*wl1-l7*wl7
#				pi=c7-c1
				li=l1*wl1-l5*wl5
				pi=c5-p1eff

#				wlw=wlw_gal
#				lw=(l1-l7)*wlw
#				pw=(c1*f1+c7*f7)/(f1+f7)
				wlw=wlw_gal
				lw=(l1-l5)*wlw
				pw=(p1eff*f1+c5*f5)/(f1+f5)
				#print "wlw,l1,l7,lw=",wlw,l1,l7,lw
				#print "c1,c7,pw=",c1,c7,pw

				wln=wln_gal
#				lc=(l1*f1-l7*f7)*wln/(f1-f7)
#				pc=(c1*f12-c7*f72)/(f12-f72)
				lc=(l1*f1-l5*f5)*wln/(f1-f5)
				pc=(p1eff*f12-c5*f52)/(f12-f52)

       #                         print "c1,length(c1)= "c1,length(c1)
       #                         print "l1,length(l1)= "l1,length(l1)
       #                         print "c5,length(c5)= "c5,length(c5)
       #                         print "l5,length(l5)= "l5,length(l5)
       #                         print "c7,length(c7)= "c7,length(c7)
       #                         print "l7,length(l7)= "l7,length(l7)
	#			print "Before: gnss_system= "gnss_system
                        	if( c7!=blank14 && l7!=blank14 ){
					gnss_system="galileo"
					wlew=wlew_gal
					lew=(l7-l5)*wlew
					pew=(c7*f7+c5*f5)/(f7+f5)
				}
#				print "AFTER: gnss_system= "gnss_system
			}
			else
			{
				gnss_system="unknown"
				#print "ERROR: unsuported gnss_system= "gnss_system > "OBS_2_OB1.v2.log"
				#print "ERROR: unsuported gnss_system= "gnss_system 
				print "WARNING: it appears as unsuported gnss_system or incomplete data " > "OBS_2_OB1.v2.log"
				print "gnss_system= "gnss_system  > "OBS_2_OB1.v2.log"
#				print "ERROR: unsuported gnss_system= "gnss_system 
#				exit -2
			}
		}

		#print gnss_system,li,pi,lw,pw,lew,pew


		konobs=konobs+1

		yy=$3
		mm=$4
		dd=$5
		ho=$6
		mi=$7
		se=$8
		tsec=ho*3600+mi*60+se
        	if(length(id)==0){
			rec=$9
		}
		else
		{
			rec=id
		}
		ksat=$10
		prn=$2

#
# WARNING: For simplicity we use the time from the beginning of month 
# in seconds. In this way an artificial general slip will
# be generated in the beginning of every month
# but this should not be in general a problem because
# the WARTK CPF used to be reset time to time 
# (this would only affect in case of being used for
# users, in the midnight of the first day of every month...)
# 
######		tmsec=mm*86400+tsec+.5
		tmsec=dd*86400+tsec+.5

		if(konobs==1){
			itmsec0=int(tmsec+.5)
			print "itmsec0= "itmsec0 > "OBS_2_OB1.v2.log"
		}
		t1sec=tmsec-itmsec0
		Bw=lw-pw
		Bew=lew-pew
		lew_w=lew-lw
##		ii=rec" "prn
#		ii=rec" "prn" "ksat
#20120607[MHP] Here it is the bug fixing:
		ii=rec" "prn" "gnss_system
		kon[ii]++

		#print "konobs,tmsec,t1sec,ii,lw,pw,Bw=",konobs,tmsec,t1sec,ii,lw,pw,Bw

		if ( length(t1sec0[ii])!=0 ) {
#
			dtsec=t1sec-t1sec0[ii]

			#print "dtsec,dtsecmax,dtsecmax2,gnss_system= ",dtsec,dtsecmax,dtsecmax2,gnss_system
			if(dtsec*dtsec > dtsecmax2){
				cycleslip_dtsec="T"
			}
			else
			{
				cycleslip_dtsec="F"
			}
			#print "ii,dtsec,dtsecmax,cycleslip_dtsec= ",ii,dtsec,dtsecmax,cycleslip_dtsec
#
			dBw=Bw-Bw0[ii]
			if(dBw*dBw > dBwmax2){
				cycleslip_dBw="T"
			}
			else
			{
				cycleslip_dBw="F"
			}
#
			dBew=Bew-Bew0[ii]

			#print "ii,Bew,Bew0[ii]=",ii,Bew,Bew0[ii],dBew

			if(dBew*dBew > dBewmax2){
				cycleslip_dBew="T"
			}
			else
			{
				cycleslip_dBew="F"
			}
#
			dlew_w=lew_w-lew_w0[ii]
			if(dlew_w*dlew_w > dlew_wmax2){
				cycleslip_dlew_w="T"
			}
			else
			{
				cycleslip_dlew_w="F"
			}
		}

		if ( length(li0[ii])!=0 && length(li00[ii])!=0) {

			dli=li-li0[ii]
			dtsec=t1sec-t1sec0[ii]
			dli_per_sec=dli/dtsec

			dli0=li0[ii]-li00[ii]
			dtsec0=t1sec0[ii]-t1sec00[ii]
			dli0_per_sec=dli0/dtsec0

			d2tsec=(t1sec-t1sec00[ii])/2

			#d2li=(dli_per_sec-dli0_per_sec)/d2tsec
			d2li=dli-dli0
			d2limax=d2Limax0+d2Limax_per_sec*d2tsec

				#if ( d2li*d2li > d2Limax_per_sec2 ) {
			if ( d2li*d2li > d2limax*d2limax ) {
				cycleslip_d2Li="T"
			}
			else
			{
				cycleslip_d2Li="F"
			}
		

# 
# In the beginning of the datasets ( length(karch[ii]) == 0) , an 
# initial cycle-slip must be assumed for consistency
#
#			if ( ( cycleslip_dtsec == "T" || cycleslip_d2Li == "T" || cycleslip_dBw == "T" ) || length(karch[ii]) == 0 ){

#
			if (gnss_system == "gal2"){

				if ( ( cycleslip_dtsec == "T" || cycleslip_d2Li == "T" || cycleslip_dBw == "T" ) || length(karch[ii]) == 0 ){
					cycleslip = "T"
					karch[ii]++
					lir[ii]=li

# Recomputing the reference ambiguity biases, choosen to get low
# ambiguity unknown values (avoiding any additional ill-conditioning
# of the matrix to be inverted), and taken as the multiple of the
# carrier phase wavelength closer to the corresponding pseudoranges
 	 				#b1r=l1-c1/wl1
# 	 				b1r=l1-p1/wl1
 	 				b1r=l1-p1eff/wl1
					nint(b1r,  sx)
#					ib1r[ii]=nintx*wl1
					if(tolower(integer_phase_ambiguity_alignement)=="n" || tolower(integer_phase_ambiguity_alignement)=="no"){
						ib1r[ii]=0
					}
					else
					{
						ib1r[ii]=nintx
					}
#
#					b2r=l2-p2/wl2
#					nint(b2r,  sx)
					b5r=l5-p5/wl5
					nint(b5r,  sx)
#					ib2r[ii]=nintx*wl2
					if(tolower(integer_phase_ambiguity_alignement)=="n" || tolower(integer_phase_ambiguity_alignement)=="no"){
						ib5r[ii]=0
					}	
					else	
					{
						ib5r[ii]=nintx
					}

				}

				else

				{
					cycleslip = "F"
				}

				
				#printf "%s%2d %02d %2d %2d %2d %2d%11.7f %s %1s %1d%12.9f%6d    %s    %s    %s    %s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s %5d %1s %15.7e %1s %15.7e %1s %10.4f %15.7e %1s\n","OB1 ",prn,yy,mm,dd,ho,mi,se,rec,ksat,iepochflag,recclock,4,"L1","L2","P2","P1",l1-ib1r[ii],il1as,il1sn,l2-ib2r[ii],il2as,il2sn,p2,ip2as,ip2sn,p1,ip1as,ip1sn,karch[ii],cycleslip,dtsec,cycleslip_dtsec,d2li,cycleslip_d2Li,li-lir[ii],dBw,cycleslip_dBw
				printf "%s%2d %02d %2d %2d %2d %2d%11.7f %s %1s %1d%12.9f%6d    %s    %s    %s    %s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s %5d %1s %15.7e %1s %15.7e %1s %10.4f %15.7e %1s %s\n","OB1 ",prn,yy,mm,dd,ho,mi,se,rec,ksat,iepochflag,recclock,4,"L1","L5","C5","P1",l1-ib1r[ii],il1as,il1sn,l5-ib5r[ii],il5as,il5sn,c5,ic5as,ic5sn,p1eff,ip1as,ip1sn,karch[ii],cycleslip,dtsec,cycleslip_dtsec,d2li,cycleslip_d2Li,li-lir[ii],dBw,cycleslip_dBw,gnss_system

			}

			if (gnss_system == "galileo"){

				if ( ( cycleslip_dtsec == "T" || cycleslip_d2Li == "T" || cycleslip_dBw == "T" || cycleslip_dlew_w == "T" || cycleslip_dBew == "T" ) || length(karch[ii]) == 0 ){
					cycleslip = "T"
					karch[ii]++
					lir[ii]=li

# For Galileo observations (at the time being only simulated)
# NO integer-cycles adjustment with the code is done
# (for checking of results, because the biases and DCBs are zero)
#
                                        b1r=l1-p1eff/wl1
                                        nint(b1r,  sx)
#                                        ib1r[ii]=nintx
#                                        ib1r[ii]=0
					if(tolower(integer_phase_ambiguity_alignement)=="n" || tolower(integer_phase_ambiguity_alignement)=="no"){
						ib1r[ii]=0
					}	
					else	
					{
						ib1r[ii]=nintx
					}

#
                                	b5r=l5-c5/wl5
                                	nint(b5r,  sx)
#                                	ib5r[ii]=nintx
#                                	ib5r[ii]=0
					if(tolower(integer_phase_ambiguity_alignement)=="n" || tolower(integer_phase_ambiguity_alignement)=="no"){
						ib5r[ii]=0
					}	
					else	
					{
						ib5r[ii]=nintx
					}

                                	b7r=l7-c7/wl7
                                	nint(b7r,  sx)
#                               	ib7r[ii]=nintx
#                                	ib7r[ii]=0
					if(tolower(integer_phase_ambiguity_alignement)=="n" || tolower(integer_phase_ambiguity_alignement)=="no"){
						ib7r[ii]=0
					}	
					else	
					{
						ib7r[ii]=nintx
					}
				}

				else
				{
					cycleslip = "F"
				}

					printf "%s%2d %02d %2d %2d %2d %2d%11.7f %s %1s %1d%12.9f%6d    %s    %s    %s    %s    %s    %s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s %5d %1s %15.7e %1s %15.7e %1s %10.4f %15.7e %1s %15.7e %1s %15.7e %1s %s\n","OB1 ",prn,yy,mm,dd,ho,mi,se,rec,ksat,iepochflag,recclock,6,"L1","L5","C5","P1","L7","C7",l1-ib1r[ii],il1as,il1sn,l5-ib5r[ii],il5as,il5sn,c5,ic5as,ic5sn,p1eff,ip1as,ip1sn,l7-ib7r[ii],il7as,il7sn,c7,ic7as,ic7sn,karch[ii],cycleslip,dtsec,cycleslip_dtsec,d2li,cycleslip_d2Li,li-lir[ii],dBw,cycleslip_dBw,dBew,cycleslip_dBew,dlew_w,cycleslip_dlew_w,gnss_system
			}
#
			if (gnss_system == "gps"){

				if ( ( cycleslip_dtsec == "T" || cycleslip_d2Li == "T" || cycleslip_dBw == "T" ) || length(karch[ii]) == 0 ){
					cycleslip = "T"
					karch[ii]++
					lir[ii]=li

# Recomputing the reference ambiguity biases, choosen to get low
# ambiguity unknown values (avoiding any additional ill-conditioning
# of the matrix to be inverted), and taken as the multiple of the
# carrier phase wavelength closer to the corresponding pseudoranges
					if ( pi_abs > pi_abs_max ){
 	 					b1r=l1-c1/wl1
					}
					else
					{
 	 					b1r=l1-p1/wl1
					}
					nint(b1r,  sx)
#					ib1r[ii]=nintx*wl1
					if(tolower(integer_phase_ambiguity_alignement)=="n" || tolower(integer_phase_ambiguity_alignement)=="no"){
						ib1r[ii]=0
					}
					else
					{
						ib1r[ii]=nintx
					}
#
#					b2r=(l2-p2)/wl2
					b2r=l2-p2/wl2
					nint(b2r,  sx)
#					ib2r[ii]=nintx*wl2
					if(tolower(integer_phase_ambiguity_alignement)=="n" || tolower(integer_phase_ambiguity_alignement)=="no"){
						ib2r[ii]=0
					}	
					else	
					{
						ib2r[ii]=nintx
					}

				}

				else

				{
					cycleslip = "F"
				}

				
				#printf "%s%2d %02d %2d %2d %2d %2d%11.7f %s %1s %1d%12.9f%6d    %s    %s    %s    %s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s %5d %1s %15.7e %1s %15.7e %1s %10.4f %15.7e %1s\n","OB1 ",prn,yy,mm,dd,ho,mi,se,rec,ksat,iepochflag,recclock,4,"L1","L2","P2","C1",l1-ib1r[ii],il1as,il1sn,l2-ib2r[ii],il2as,il2sn,p2,ip2as,ip2sn,c1,ic1as,ic1sn,karch[ii],cycleslip,dtsec,cycleslip_dtsec,d2li,cycleslip_d2Li,li-lir[ii],dBw,cycleslip_dBw
				if ( pi_abs > pi_abs_max ){
					printf "%s%2d %02d %2d %2d %2d %2d%11.7f %s %1s %1d%12.9f%6d    %s    %s    %s    %s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s %5d %1s %15.7e %1s %15.7e %1s %10.4f %15.7e %1s %s\n","OB1 ",prn,yy,mm,dd,ho,mi,se,rec,ksat,iepochflag,recclock,4,"L1","L2","P2","C1",l1-ib1r[ii],il1as,il1sn,l2-ib2r[ii],il2as,il2sn,p2,ip2as,ip2sn,c1,ic1as,ic1sn,karch[ii],cycleslip,dtsec,cycleslip_dtsec,d2li,cycleslip_d2Li,li-lir[ii],dBw,cycleslip_dBw,gnss_system
				}
				else
				{
					printf "%s%2d %02d %2d %2d %2d %2d%11.7f %s %1s %1d%12.9f%6d    %s    %s    %s    %s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s %5d %1s %15.7e %1s %15.7e %1s %10.4f %15.7e %1s %s\n","OB1 ",prn,yy,mm,dd,ho,mi,se,rec,ksat,iepochflag,recclock,4,"L1","L2","P2","P1",l1-ib1r[ii],il1as,il1sn,l2-ib2r[ii],il2as,il2sn,p2,ip2as,ip2sn,p1,ip1as,ip1sn,karch[ii],cycleslip,dtsec,cycleslip_dtsec,d2li,cycleslip_d2Li,li-lir[ii],dBw,cycleslip_dBw,gnss_system
				}

			}

#			if (gnss_system == "next_gps"){
#
#				print "ERROR: unsuported "gnss_system > "OBS_2_OB1.v2.log"
#				print "ERROR: unsuported "gnss_system 
#				exit -2
#
#			}
			if (gnss_system == "next_gps"){

				if ( ( cycleslip_dtsec == "T" || cycleslip_d2Li == "T" || cycleslip_dBw == "T" || cycleslip_dlew_w == "T" || cycleslip_dBew == "T" ) || length(karch[ii]) == 0 ){
					cycleslip = "T"
					karch[ii]++
					lir[ii]=li

# For Galileo observations (at the time being only simulated)
# NO integer-cycles adjustment with the code is done
# (for checking of results, because the biases and DCBs are zero)
#
                                        b1r=l1-p1/wl1
                                        nint(b1r,  sx)
#                                        ib1r[ii]=nintx
#                                        ib1r[ii]=0
					if(tolower(integer_phase_ambiguity_alignement)=="n" || tolower(integer_phase_ambiguity_alignement)=="no"){
						ib1r[ii]=0
					}	
					else	
					{
						ib1r[ii]=nintx
					}

                                	b5r=l5-c5/wl5
                                	nint(b5r,  sx)
#                                	ib5r[ii]=nintx
#                                	ib5r[ii]=0
					if(tolower(integer_phase_ambiguity_alignement)=="n" || tolower(integer_phase_ambiguity_alignement)=="no"){
						ib5r[ii]=0
					}	
					else	
					{
						ib5r[ii]=nintx
					}

#
#                                	b7r=l7-c7/wl7
#                                	nint(b7r,  sx)
#                                	ib7r[ii]=0
                                	b2r=l2-p2/wl2
                                	nint(b2r,  sx)
                                	ib2r[ii]=0
					if(tolower(integer_phase_ambiguity_alignement)=="n" || tolower(integer_phase_ambiguity_alignement)=="no"){
						ib2r[ii]=0
					}	
					else	
					{
						ib2r[ii]=nintx
					}
				}

				else
				{
					cycleslip = "F"
				}

					printf "%s%2d %02d %2d %2d %2d %2d%11.7f %s %1s %1d%12.9f%6d    %s    %s    %s    %s    %s    %s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s%14.3f%1s%1s %5d %1s %15.7e %1s %15.7e %1s %10.4f %15.7e %1s %15.7e %1s %15.7e %1s %s\n","OB1 ",prn,yy,mm,dd,ho,mi,se,rec,ksat,iepochflag,recclock,6,"L1","L2","P2","P1","L5","C5",l1-ib1r[ii],il1as,il1sn,l2-ib2r[ii],il2as,il2sn,p2,ip2as,ip2sn,p1,ip1as,ip1sn,l5-ib5r[ii],il5as,il5sn,c5,ic5as,ic5sn,karch[ii],cycleslip,dtsec,cycleslip_dtsec,d2li,cycleslip_d2Li,li-lir[ii],dBw,cycleslip_dBw,dBew,cycleslip_dBew,dlew_w,cycleslip_dlew_w,gnss_system

#l5-ib5r[ii],il5as,il5sn,c1,ic1as,ic1sn,c7,ic7as,ic7sn,c5,ic5as,ic5sn,karch[ii],cycleslip,dtsec,cycleslip_dtsec,d2li,cycleslip_d2Li,li-lir[ii],dBw,cycleslip_dBw,dBew,cycleslip_dBew,dlew_w,cycleslip_dlew_w
			}
#

		}

		t1sec00[ii]=t1sec0[ii]
		t1sec0[ii]=t1sec

		Bw0[ii]=Bw
		Bew0[ii]=Bew
		lew_w0[ii]=lew_w

		li00[ii]=li0[ii]
		li0[ii]=li

#		if ( length(t1sec0[ii0])!=0 && length(t1sec0[ii00])!=0 ) {

		#printf "%02d %2d %2d %13.7f %s %2d %14.4f %13.3f %14.4f %14.4f %13.3f %14.4f %14.4f %13.3f %14.4f\n",yy,mm,dd,tsec,rec,prn,li,pi,li-pi,lw,pw,lw-pw,lc,pc,lc-pc
	}
	else
        {
#		print "WARNING: rejected observation nm= "nm" != 4 && != 6" > "OBS_2_OB1.v2.log"
		print "WARNING: rejected observation nm= "nm" < 4" > "OBS_2_OB1.v2.log"
		print "Record: " > "OBS_2_OB1.v2.log"
	}
}	

