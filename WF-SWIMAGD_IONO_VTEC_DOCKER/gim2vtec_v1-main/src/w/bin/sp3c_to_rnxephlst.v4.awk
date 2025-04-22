#070924: Main difference regarding to version 3: inclusion of orbflag as last
#        binary field (for the time being all the time equal to zero)
{
	if(substr($0,1,1)=="*" && substr($0,2,1)==" " && NF==7){
		year=$2
		yy=substr(year,3,2)
		month=$3
		day=$4
		hh=$5
		mm=$6
		ss=$7
	}

#	if(substr($0,1,2)=="PG" || substr($0,1,2)=="P "){
	if(substr($0,1,2)=="PG" || substr($0,1,2)=="P " || substr($0,1,2)=="PL" || substr($0,1,2)=="PE"){
#		prn=substr($1,3,2)
		prn=substr($0,3,2)
#		x=$2
#		y=$3
#		z=$4
#		dt=$5
		x=substr($0,6,13)
		y=substr($0,20,13)
		z=substr($0,34,13)
		dt=substr($0,48,13)
#		sx=$6
#		sy=$7
#		sz=$8
#
# The orbital flag is initially set to zero in this version (no apriori issue)
#
                orbflag=0

#		printf "S3C %2d %02d %2d %2d %2d %2d %11.8f %13.6f %13.6f %13.6f %13.6f",prn,yy,month,day,hh,mm,ss,x,y,z,dt
		printf "S3C %2d %02d %2d %2d %2d %2d %11.8f %13.6f %13.6f %13.6f %13.6f %1d",prn,yy,month,day,hh,mm,ss,x,y,z,dt,orbflag

		if(dt != 999999.999999){
			sdt=$9	
			printf " %3d\n",sdt
		}
		else
		{
			printf "\n"
		}

	}

}
