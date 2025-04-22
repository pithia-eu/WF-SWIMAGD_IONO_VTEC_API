#BEGIN{pi=3.1415927;gdmin=6300;gdmax=6450}
BEGIN{pi=atan2(1,1)*4;gdmin=6300;gdmax=6450}
{
 rec=$1
 x=$2;y=$3;z=$4;
 ra=atan2(y,x)*180./pi
 if(ra < 0){ra=ra+360.}
 r=sqrt(x*x+y*y) 
 dec=atan2(z,r)*180./pi
#Geocentric distance filter
 gd=sqrt(x*x+y*y+z*z)/1000.000
 if(gd>=gdmin && gd<=gdmax){
 	#printf "%s %11.6f %11.6f %11.5f\n",$1,ra,dec,gd
 	printf "%s %14.9f %14.9f %13.7f\n",$1,ra,dec,gd
	}
 else
	{
	 print rec" GD-ERROR: geocentric distance "gd" out of allowable range "gdmin" to "gdmax
	}
}
