BEGIN{
	end_of_header = 0
}
{
	if ( length($0) >= 73 ){
		if ( substr($0,61,13) == "END OF HEADER" ) {
			end_of_header = 1
		}
	}

	if ( end_of_header == 0 ) {
		print $0
	}
	else
	{
		if ( length($0) == 32 && substr($0,28,1) == " " && substr($0,30,1) == " " && substr($0,29,1) == 4 ){
			njump=$NF

			for ( i = 1 ; i <= njump ; i++ ){
				getline
			}

		}
		else
		{
			print $0
		}
	}
}
