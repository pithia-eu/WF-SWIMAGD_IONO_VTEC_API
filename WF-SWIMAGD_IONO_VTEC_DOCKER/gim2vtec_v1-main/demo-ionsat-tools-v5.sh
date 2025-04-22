netfile=".netrc"
if grep -q USERNAME "$netfile"; then
    #echo "[USERNAME]/[PASSWORD] found in .netrc file, please update it to proceed"
    echo "Warning: [USERNAME]/[PASSWORD] found in .netrc file; please update it to proceed in case you need GIMs outside PITHIA-NRF eScience center"
    #exit 1
fi
if [ ! -d "target" ]; then
  echo "./target directory does not exist, creating"
  mkdir target
fi

docker build -t ionsat/tools-v5:1 .
#docker run --mount type=bind,source="$(pwd)"/target,target=/root/run/AUDITOR/VTECvsLAT_from_GIM.uqrg.4.556064337 ionsat/tools-v5:1 ./run-test-ionsat.scr
docker run --mount type=bind,source="$(pwd)"/target,target=/root/run/May2024storm ionsat/tools-v5:1 ./run-test-ionsat.scr
pqiv -i target/VTECvsTIME_from_GIM.*/*png
pqiv -i  target/VTECvsLAT_from_GIM.uqrg.*/movie/*anim.gif
#xdg-open target/movie/ionex_2_latitudinal_VTEC_profiles_time_series.uqrg.2017.163-164.anim.gif
