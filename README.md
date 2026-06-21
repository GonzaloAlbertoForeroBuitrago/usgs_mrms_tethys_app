
 ## USGS-MRMS  Flood Explorer

Web app designed to suppport state-scale operational flood awareness and flood signature exploration, processing 572,332,774 pixels across the United States in less than one minute. 

The aplication integrates data from 8,616 USGS basins and Multi Radar Multi Sensor (MRMS) Radar-Only Rainfall products into a database containing 269,751 water stage peak values and the corresponding 12 hours of antecedent rainfall for each peak. 

An integrated python package provides the back end processing capabilities including peak extraction, basin delineation, mask generation, MRMS data download and rainfall Processing.

# Local Installation Guide 

This guide explains how to install the Tethys application and the associated Python backend package.

## Repositories

Application:

```bash
https://github.com/GonzaloAlbertoForeroBuitrago/usgs_mrms_tethys_app.git
```

Python package:

```bash
https://github.com/GonzaloAlbertoForeroBuitrago/mrms_usgs_events.git
```

## 1. Install Xcode Command Line Tools

```bash
xcode-select --install
```

## 2. Create a Local Project Folder

```bash
mkdir -p ~/tethys_flood_local
cd ~/tethys_flood_local
```

## 3. Clone Both Repositories

```bash
git clone https://github.com/GonzaloAlbertoForeroBuitrago/usgs_mrms_tethys_app.git
git clone https://github.com/GonzaloAlbertoForeroBuitrago/mrms_usgs_events.git
```

## 4. Install Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## 5. Install Micromamba

```bash
brew install micromamba
```

## 6. Initialize Micromamba

```bash
micromamba shell init -s zsh -r ~/micromamba
source ~/.zshrc
```

## 7. Create the Tethys Environment

Only install the core environment requirements manually. 
The remaining app dependencies will be installed later through `install.yml`.

```bash
micromamba create -n tethys_flood -c conda-forge \
  python=3.11 \
  tethys-platform \
  gdal \
  libgdal-grib \
  -y
```

## 8. Activate the Environment

```bash
micromamba activate tethys_flood
```

## 9. Install the Python Backend Package

```bash
cd ~/tethys_flood_local/mrms_usgs_events
python -m pip install --upgrade pip
pip install -e .
```

## 10. Verify the Package Installation

```bash
mrms-usgs --help
```

## 11. Verify GDAL and GRIB Support

```bash
gdalinfo --formats | grep -i grib
```

## 12. Verify Tethys Platform

```bash
tethys version
```

## 13. Initialize Tethys

```bash
tethys quickstart
```

## 14. Install the Tethys App

```bash
cd ~/tethys_flood_local/usgs_mrms_tethys_app/tethysapp-usgs_mrms
tethys install -d -f install.yml
```

## 15. Start the Tethys Portal

```bash
tethys start
```

Then open the local Tethys portal in the browser:

```bash
http://127.0.0.1:8000
```




Acknowledgements
This material is based upon work supported by the U.S. National Science Foundation under Grant No. TI-2303756 and the Tethys Geoscience Foundation.
