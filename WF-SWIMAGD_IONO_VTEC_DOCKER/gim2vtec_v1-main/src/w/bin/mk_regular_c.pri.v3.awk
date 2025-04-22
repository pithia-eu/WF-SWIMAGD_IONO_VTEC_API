BEGIN{
	if(length(lat0)==0)lat0=-80
	if(length(lat1)==0)lat1=80
	if(length(dlon)==0)dlon=8
	if(length(dlat)==0)dlat=4
	if(length(nlayers)==0){
		nlayers=2
		h[1]=450
		h[2]=1130
#		print ERRNO
		getline < "hm_layers.tmp" 
#		print ERRNO
		if ( ERRNO == "0"){
			nlayers=NF
			for(i=1;i<=NF;i++){
				h[i]=$i
			}
		}
	}
#	print "dlon,dlat,nlayers,h=",dlon,dlat,nlayers
#	for(i=1;i<=nlayers;i++){
#		printf " %s",h[i]
#	}
#	printf "\n"
	
	lat1_lat0 = lat1-lat0
	for(i=1;i<=int(360/dlon);i++)
		#for(j=1;j<=int(160/dlat);j++) 
		for(j=1;j<=int(lat1_lat0/dlat);j++) 
			for(k=1;k<=nlayers;k++) 
					#printf "%4d %7.2f %6.2f %4d %4d %3d %s %s\n",h[k],dlon*(i-0.5),dlat*(j-0.5)+10-90,i,j,k,"0.0001","0.05"
					printf "%4d %7.2f %6.2f %4d %4d %3d %s %s\n",h[k],dlon*(i-0.5),dlat*(j-0.5)+lat0,i,j,k,"0.0001","0.05"
}
