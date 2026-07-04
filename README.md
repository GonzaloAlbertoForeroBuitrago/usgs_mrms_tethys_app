
 ## USGS-MRMS  Flood Explorer

The application consists of two modules: Historical Exploration and
Flood Alerts.

The Flood Alerts module, demonstrated using the Mystic Camp flood
event on July 4, 2025, showed that maximum pixel rainfall can provide
an early signal, detecting the flood nearly two hours before the peak
water stage. This suggests that pixel-based rainfall can support early
flood warnings using observed rainfall at the state scale.

The app combines operational flood alerts with historical rainfall
exploration through a Python package developed as the project's
backend. Using this package, we build a rainfall–water stage database
from the thirty-one highest water stage peaks across 8,616 USGS
basins. The package performs peak extraction, basin delineation, mask
generation, state-scale MRMS downloads in less than one minute, and
Zarr conversion. This fast processing enables state-based operational
analyses across the entire United States using real observations.

Although the methodology can continue to be improved, it provides a
flexible foundation for future research and collaborations are welcome
to expand and refine its capabilities.


## 🎥 Operational Demonstration of the Python Package in the "USGS MRMS Flood Explorer" Web Application 

▶️ **[Demonstration](https://www.youtube.com/watch?v=hVZSRkVBx9g)**

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
