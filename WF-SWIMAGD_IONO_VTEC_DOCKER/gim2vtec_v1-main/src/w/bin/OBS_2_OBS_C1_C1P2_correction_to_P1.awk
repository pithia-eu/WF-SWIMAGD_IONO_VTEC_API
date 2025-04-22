#20080327: The main difference of this script 
# OBS_2_OBS_C1_C1P2_correction_to_P1.awk
# regarding to OB1_2_OB1_C1-CP1.awk is that:
# 1) This corrects directly OBS records (previous to OB1)
# 2) It can use as options (input variable cp1_class as C1 or C1P2): 
#  C1 or C1P2 corrections (corresponding # to C1-P1 classes 2 and 1 in file 
#  ~/w/dat/GPS_Receiver_Types, respectively.
#20080325: This script is intended to correct the C1-P1 DCBs (for satellites, and if available for receivers), in order to make C1 as P1-DCB compliant (i.e. DCB(PC)=0) in order to be able to generate comparable satellite clocks, with those of IGS for example.
BEGIN{
	if(length(cp1_class)==0){
		print "ERROR: external variable cp1_class (C1 or C1P2) mandatory"
		exit -2
	}

	getline < "C1-P1.all.s"
	n=NF/3
	for(i=1;i<=n;i++){
		i1=3*(i-1)+1
		i2=i1+1
		i3=i2+1
		id=$(i1)
		if(length(id)>2){
			c1_p1_rec[id]=$(i2)
			sc1_p1_rec[id]=$(i3)
			#print "id,c1_p1_rec[id],sc1_p1_rec[id]= "id,c1_p1_rec[id],sc1_p1_rec[id]
		}
		else
		{
			id1=+id
			c1_p1_prn[id1]=$(i2)
			sc1_p1_prn[id1]=$(i3)
			#print "id1,c1_p1_prn[id1],sc1_p1_prn[id1]= "id1,c1_p1_prn[id1],sc1_p1_prn[id1]
		}
	}
}
{
if( substr($0,1,4) == "OBS ") {
	rec=substr($0,34,4)
	prn=+substr($0,5,2)
	nobs=+substr($0,58,2)
        ic1=0
        ip2=0
	for(i=1;i<=nobs;i++){
		i1=64+(i-1)*6
		ko=substr($0,i1,2)
		if(ko=="C1"){
			ic1=i
		}
		if(ko=="P2"){
			ip2=i
		}
	}
	if(ic1!=0){

		iic1=64+(nobs-1)*6+2+(ic1-1)*16
#		c1=substr($0,iic1,16)
		c1=+substr($0,iic1,14)
#                print "c1full= "substr($0,iic1,16)
#		print "c1= "c1

	}

	if(ip2!=0){

		iip2=64+(nobs-1)*6+2+(ip2-1)*16
#		c1=substr($0,iic1,16)
		p2=+substr($0,iip2,14)
#                print "c1full= "substr($0,iic1,16)
#		print "c1= "c1

	}

#C1 correction by default
	if(length(c1_p1_prn[prn])!=0 && cp1_class != "C1P2"){
		c1_cp1=c1-c1_p1_prn[prn]
#		print "rec,prn,c1_p1_prn[prn],c1_cp1=",rec,prn,c1_p1_prn[prn],c1_cp1
		if(length(c1_p1_rec[rec])!=0){
			c1_cp1=c1_cp1-c1_p1_rec[rec]
#			print "rec,c1_p1_rec[rec],c1_cp1=",rec,c1_p1_rec[rec],c1_cp1
		}

#		printf "*\n"
		printf "%s%14.3f%s\n",substr($0,1,iic1-1),c1_cp1,substr($0,iic1+14)
#		printf "%s\n",$0
	}

#C1 and P2 correction
	if(length(c1_p1_prn[prn])!=0 && cp1_class == "C1P2"){
		c1_cp1=c1-c1_p1_prn[prn]
		p2_cp1=p2-c1_p1_prn[prn]
#		print "rec,prn,c1_p1_prn[prn],c1_cp1=",rec,prn,c1_p1_prn[prn],c1_cp1
		if(length(c1_p1_rec[rec])!=0){
			c1_cp1=c1_cp1-c1_p1_rec[rec]
			p2_cp1=p2_cp1-c1_p1_rec[rec]
#			print "rec,c1_p1_rec[rec],c1_cp1=",rec,c1_p1_rec[rec],c1_cp1
		}

                if ( iic1 < iip2 ) {
			ii1=iic1
			ii2=iip2
			obs1=c1_cp1
			obs2=p2_cp1
		}
		else
		{
			ii1=iip2
			ii2=iic1
			obs1=p2_cp1
			obs2=c1_cp1
		}

#		printf "**\n"
#		#printf "%s%14.3f%s\n",substr($0,1,iic1-1),c1_cp1,substr($0,iic1+14)
		printf "%s%14.3f%s%14.3f%s\n",substr($0,1,ii1-1),obs1,substr($0,ii1+14,ii2-ii1-14),obs2,substr($0,ii2+14)
#		printf "%s\n",$0
	}

}
else
{
	print $0
}
}
