# Docker IonSAT-tools

- Application to run IonSAT-tools inside a docker container.

## Requirements

### Docker

* [Docker Engine](https://docs.docker.com/engine/install/) 

The docker engine needs to be installed to run the application. Once this is done it is recommended to add docker to the sudoers group (explained in [this link](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user))

## Quick user guide

Get the repository locally:

```bash
git clone https://gitlab.upc.edu/ionsat/gim2vtec_v1
cd gim2vtec_v1
```

Build the image the first time (you must be in the same folder as the Dockerfile):

```bash
docker build -t ionsat/tools-v5 .
```

Create the target folder to share the results and repo for common files, and create the sta_pos.tot file from the default one:

```bash
mkdir -p target
cp src/dat/sta_pos.tot.default target/sta_pos.tot
```

Run the docker image sharing the `target` folder with your desired parameters.

Be sure you are in the parent folder of `target`:

Run gim2vtec.v2b.scr to see the usage parameters:

```bash
docker run --mount type=bind,source="$(pwd)"/target,target=/root/run/ ionsat/tools-v5 ./w/bin/gim2vtec.v2b.scr
```

### Example execution

Specify your `EXECUTION_ID` (don't remove the `run/` before that) to find the results in your local folder `target/EXECUTION_ID`

```bash
docker run --mount type=bind,source="$(pwd)"/target,target=/root/run/ ionsat/tools-v5 ./w/bin/gim2vtec.v2b.scr VTECvsTIME 2024 5 8 2024 5 9 uqrg 120 run/EXECUTION_ID nn VTECvsTIME_extraction ebre jplm
```

This will also create the `target/sta_pos.tot` file which you will be able to [modify](#introducing-new-locations).

See the results:

```bash
ls -ltr target/EXECUTION_ID
```
**IMPORTANT**:
After the first run, the `datasets` folder (to cache ionex downloads) and the [sta_pos.tot](#introducing-new-locations) file will be created inside the `target` folder if they didn't exist already.

Be careful not to name your `EXECUTION_ID` as `"datasets"` or `"sta_pos.tot"` as this will override these necessary folders/files.


### Introducing new locations
Important: you can introduce new locations / facilities, where the VTEC time series should be extracted from the GIMs, by editing the `sta_pos.tot` file. 

The project contains a default file [src/dat/sta_pos.tot.default](src/dat/sta_pos.tot.default) that should not be updated (as the docker image won't see the changes unless built again). Instead, you can modify the file found in `target` which will exist after a first run as indicated [above](#example-execution) or you may have copied from the default file.

Once the `target/sta_pos.tot` file is present in your local machine, you can perform any changes as desired before running the software.

The `sta_pos.tot` file contains one location per line, with the following four fields separated by blanks,
- field#1: 4 digits location Id (e.g. invr)
- field#2: Geographic longitude / degrees (e.g. 355.8)
- field#3: Geographic spherical latitude / degrees (e.g. 57.3)
- field#4: Geocentric distance / km, e.g. 6363.03, or in case this is not known, the mean Earth radius (6370.0) can be used in general, because the VTEC series does not depend on the geocentric distance.

See for example (extracted from the actual file [src/dat/sta_pos.tot.default](src/dat/sta_pos.tot.default):

```
invr  355.780742133   57.311575041  6363.0336940
osls   10.367760663   59.568796010  6362.4395777
vlis    3.597331273   51.255163371  6365.1573044
tmp1   40          18         6379
i_bo  254.7  40    6370
i_au  262.3  30.4  6370
i_mh  288.5  42.6  6370
```

