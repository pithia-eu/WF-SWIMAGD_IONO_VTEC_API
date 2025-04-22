BEGIN{
      itecmap=0
      digits_per_value=5
      line_length=80 
      values_per_line=int(line_length/digits_per_value)
      print "digits_per_value,line_length,values_per_line=",digits_per_value,line_length,values_per_line > "temp.log"
      tec_instead_of_rms=1
     }
     {

      if(substr($0,61,18)=="EPOCH OF FIRST MAP"){
                                                 year0=$1
                                                 month0=$2
                                                 day0=$3
                                                 hour0=$4
                                                 minute0=$5
                                                 seconds0=$6
                                                 print year0,month0,day0,hour0,minute0,seconds0 > "t_lat_lon.info"
                                                }

      if(substr($0,61,17)=="EPOCH OF LAST MAP"){
                                                 year1=$1
                                                 month1=$2
                                                 day1=$3
                                                 hour1=$4
                                                 minute1=$5
                                                 seconds1=$6
                                                 print year1,month1,day1,hour1,minute1,seconds1 > "t_lat_lon.info"
                                                }


      if(substr($0,61,8)=="INTERVAL"){
                                      interval=$1
                                      print interval > "t_lat_lon.info"
                                     }

      if(substr($0,61,17)=="# OF MAPS IN FILE"){
                                                nmaps=$1
                                                print nmaps > "t_lat_lon.info"
                                               }

      if(substr($0,61,11)=="BASE RADIUS"){
                                            bradius=$1 
                                            print bradius > "t_lat_lon.info"
                                           }

      if(substr($0,61,18)=="HGT1 / HGT2 / DHGT"){
                                            height0=$1   
                                            height1=$2
                                            dheight=$3
                                            print height0,height1,dheight > "t_lat_lon.info"
                                           }

      if(substr($0,61,13)=="MAP DIMENSION"){
                                            mapdim=$1
                                            print mapdim > "t_lat_lon.info"
                                           }

      if(substr($0,61,18)=="LAT1 / LAT2 / DLAT"){
                                                 lat0=+substr($0,4,5)
                                                 lat1=+substr($0,10,5)
                                                 dlat=+substr($0,16,5)
                                                 print lat0,lat1,dlat > "t_lat_lon.info"
                                                } 
      if(substr($0,61,18)=="LON1 / LON2 / DLON"){
                                                 lon00=+substr($0,3,6)
                                                 lon11=+substr($0,9,6)
                                                 dlon0=+substr($0,15,6)
                                                 print lon00,lon11,dlon0 > "t_lat_lon.info"

                                                } 

      if(substr($0,61,8)=="EXPONENT"){
                                                 exponent=$1
                                                 print exponent > "t_lat_lon.info"

                                                }

      if(substr($0,61,16)=="PRN / BIAS / RMS"){
                                                 print substr($0,1,26) > "dcbs.satellites"

						if(substr($0,4,1)==" " || substr($0,4,1)=="G"){
							print substr($0,5,2),substr($0,8,9),substr($0,18,9) > "dcbs.satellites.gps"
							}
						else
							{

							if(substr($0,4,1)=="R"){
								print substr($0,5,2),substr($0,8,9),substr($0,18,9) > "dcbs.satellites.glonass"
								}
							else
								{
	
								if(substr($0,4,1)=="C"){
									print substr($0,5,2),substr($0,8,9),substr($0,18,9) > "dcbs.satellites.beidou"
									}
								else
									{
		
									if(substr($0,4,1)=="E"){
										print substr($0,5,2),substr($0,8,9),substr($0,18,9) > "dcbs.satellites.galileo"
										}
									else
										{
		
										print "ERROR: unknown kind of satellite: "substr($0,4,1)
										print "EXECUTION ABORTED"
										exit -2
		
										}
									}
								}

							}

                                                }

      if(substr($0,61,20)=="STATION / BIAS / RMS"){

                                                print substr($0,1,46) > "dcbs.stations"


						if(substr($0,4,1)==" " || substr($0,4,1)=="G"){

							print tolower(substr($0,7,4)),substr($0,28,9),substr($0,38,9) > "dcbs.stations.gps"

							}
						else
							{

							if(substr($0,4,1)=="R"){
								#print substr($0,5,2),substr($0,8,9),substr($0,18,9) > "dcbs.satellites.glonass"
								print tolower(substr($0,7,4)),substr($0,28,9),substr($0,38,9) > "dcbs.stations.glonass"
								}
							else
								{
	
								if(substr($0,4,1)=="C"){
									#print substr($0,5,2),substr($0,8,9),substr($0,18,9) > "dcbs.satellites.glonass"
									print tolower(substr($0,7,4)),substr($0,28,9),substr($0,38,9) > "dcbs.stations.beidou"
									}
								else
									{
		
									if(substr($0,4,1)=="E"){
										#print substr($0,5,2),substr($0,8,9),substr($0,18,9) > "dcbs.satellites.glonass"
										print tolower(substr($0,7,4)),substr($0,28,9),substr($0,38,9) > "dcbs.stations.galileo"
										}
									else
										{
		
										print "ERROR: unknown kind of station: "substr($0,4,1)
										print "EXECUTION ABORTED"
										exit -2
		
										}
									}
								}

							}
                                                }


      if(substr($0,61,16)=="START OF TEC MAP"){
                                               itecmap=+substr($0,2,5)
                                               itmf=itecmap
                                               if(itecmap<10)itmf="0"itmf
                                               if(itecmap<100)itmf="0"itmf
                                               ilat=0
                                               tec_instead_of_rms=1 
                                              }

      if(substr($0,61,16)=="START OF RMS MAP"){
                                               itecmap=+substr($0,2,5)
                                               itmf=itecmap
                                               if(itecmap<10)itmf="0"itmf
                                               if(itecmap<100)itmf="0"itmf
                                               ilat=0
                                               tec_instead_of_rms=0
                                              }


      if(substr($0,61,23)=="EPOCH OF CURRENT MAP"){
                                                   year=+substr($0,3,4)
                                                   month=+substr($0,11,2)
                                                   day=+substr($0,17,2)
                                                   hour=+substr($0,23,2)
                                                   minute=+substr($0,29,2)
                                                   seconds=+substr($0,35,6)

#
# Patch to allow extracting from multiday ionex file (the interval and map number is used
# from the stating epoch, to avoid problems with the month changes, etc...)
#
#                                                   time_hours=hour+minute/60+seconds/3600
                                                   time_hours=(interval/3600)*(itmf-1)+hour0+minute0/60+seconds0/3600
#

                                                   if ( tec_instead_of_rms == 1)printf "%5.2f\n",time_hours > "info."itmf
                                                  }

      if(substr($0,61,80)=="LAT/LON1/LON2/DLON/H"){
                                                   ilat=ilat+1 

                                                   lat=+substr($0,4,5)
                                                   lon0=+substr($0,9,6)
                                                   lon1=+substr($0,15,6)
                                                   dlon=+substr($0,21,6)
                                                  
                                                   nvalues=1+(lon1-lon0)/dlon
                                                   nlines=int(nvalues*digits_per_value/line_length)+1
                                                   values_to_read_last_line=nvalues-(nlines-1)*values_per_line

                                                   iline=1
                                                   nvalues_read=0
                                                   ivalt=0

                                                   while ( iline <= nlines ){

                                                        getline
                                                        if ( iline < nlines ) {
                                                                               values_to_read=values_per_line
                                                                              }
                                                                          else
                                                                              {
                                                                               values_to_read=values_to_read_last_line
                                                                              }

                                                        for(ival=1;ival<=values_to_read;ival++){
                                                                              ivalt=ivalt+1
                                                                              lon=lon0+(ivalt-1)*dlon
                                                                              c0=1+digits_per_value*(ival-1)
                                                                              tec=+substr($0,c0,digits_per_value)
                                                                              ##printf "%4d %2d %2d %9.6f %6.1f %5.1f %5d %5d\n",year,month,day,time_hours,lon,lat,tec,ivalt
                                                                              if(tec_instead_of_rms==1){
                                                                                                      printf "%3d %3d %5d %7.2f %6.2f\n",ivalt,ilat,tec,lon,lat > "tec."itmf
                                                                                                       }
                                                                                                   else
                                                                                                       {
                                                                                                      printf "%3d %3d %5d %7.2f %6.2f\n",ivalt,ilat,tec,lon,lat > "rms."itmf
                                                                                                       } 
                                                                                                     }

                                                                iline ++ 
                                                                            }

                                                  }


#      print nmaps,lat0,lat1,dlat,lon0,lon1,dlon,itecmap,year,month,day,hour,minute,seconds





      }  
