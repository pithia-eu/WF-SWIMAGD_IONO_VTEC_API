#081211: Adoption of an standard "wartk message" format for OTL records
# See below optional external variables for date (yy ... se).
BEGIN{
	if(length(yy)==0)yy=75
	if(length(mo)==0)mo=1
	if(length(da)==0)da=1
	if(length(ho)==0)ho=0
	if(length(mi)==0)mi=0
	if(length(se)==0)se=0
}
{
	rec=$1
        printf "OT2  0 %02d %2d %2d %2d %2d %4.1f %s",yy,mo,da,ho,mi,se,rec
	for(i=1;i<=2*3*11;i++){
		printf " %12.4e",$(i+1)
	}
	printf "\n"
}
