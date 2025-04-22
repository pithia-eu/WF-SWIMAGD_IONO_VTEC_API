BEGIN{endh=0}
/# \/ TYPES OF OBSERV/{n=$1;
lobs=$(n+1);
#print n,lobs;
htobs=$0} 

/END OF HEADER/{endh=1} 

{if(endh==1){
	k++;
	if(length($0)<70)klt70++
	}
}
END{
#print k,klt70;
d=k-klt70;
#print d;
if(klt70>0.5*k && n==5 && lobs=="P1"){
	print substr(htobs,1,5)"4"substr(htobs,7,28)"  "substr(htobs,37)
	}
else{
	print htobs
	}
}
