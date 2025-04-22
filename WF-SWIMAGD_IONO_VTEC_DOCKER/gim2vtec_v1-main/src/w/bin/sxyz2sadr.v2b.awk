BEGIN{pi=3.1415927;gdmin=6300;gdmax=6450}
{
 x=$2;y=$3;z=$4;
 ra=atan2(y,x)*180./pi
 if(ra < 0){ra=ra+360.}
 r=sqrt(x*x+y*y) 
 dec=atan2(z,r)*180./pi
#Geocentric distance filter
 gd=sqrt(x*x+y*y+z*z)/1000.000
 if(gd>=gdmin && gd<=gdmax){
 	printf "%s %11.6f %11.6f %11.5f\n",$1,ra,dec,gd
	}
 else
	{
	 print "GD-ERROR_"$1 >> "sxyz2sadr.v2b.log"
	}
}
