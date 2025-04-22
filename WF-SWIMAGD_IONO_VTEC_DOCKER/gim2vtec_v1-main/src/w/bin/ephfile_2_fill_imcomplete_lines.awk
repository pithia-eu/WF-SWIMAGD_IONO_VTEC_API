BEGIN{
      str=" 0.000000000000D+00"
      end_of_header=""
     }
     {
      if(end_of_header=="OK"){
                              nstr_to_fill=(79-length($0))/19
                              if(nstr_to_fill == int(nstr_to_fill)){
                                                                    if(nstr_to_fill == 0){
                                                                                          print $0
                                                                                         }
                                                                                         else
                                                                                         {
                                                                                          printf "%s",$0
                                                                                          for(i=1;i<=nstr_to_fill;i++){
                                                                                                                       printf "%s",str
                                                                                                                      }
                                                                                          printf "\n"
                                                                                         }
                                                                   }
                                                                   else
                                                                   {
                                                                    print $0
                                                                    print "WARNING: non-integer nstr_to_fill="nstr_to_fill > "nstr_to_fill.eph.log"
                                                                   }
                             }
                             else
                             {
                              print $0
                             }
      if(length($0) >= 73){
                           if(substr($0,61,13)=="END OF HEADER"){
                                                                 end_of_header="OK"
                                                                }
                          }
      }
