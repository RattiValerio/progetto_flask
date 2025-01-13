#!/bin/bash
apt update
apt upgrade -y
apt-get install -y git
apt-get install -y make
apt-get install -y unzip

git clone https://github.com/ajnisbet/opentopodata.git
cd opentopodata

# Scarica il dataset GEBCO e configuralo
mkdir -p data/gebco
cd data/gebco
curl -0 -k https://www.bodc.ac.uk/data/open_download/gebco/gebco_2024_sub_ice_topo/geotiff/ -o geotiff
unzip geotiff
mv gebco_2024_sub_ice_n0.0_s-90.0_w0.0_e90.0.tif     S90E000.tif
mv gebco_2024_sub_ice_n0.0_s-90.0_w-180.0_e-90.0.tif S90W180.tif
mv gebco_2024_sub_ice_n0.0_s-90.0_w-90.0_e0.0.tif    S90W090.tif
mv gebco_2024_sub_ice_n0.0_s-90.0_w90.0_e180.0.tif   S90E090.tif
mv gebco_2024_sub_ice_n90.0_s0.0_w0.0_e90.0.tif      N00E000.tif
mv gebco_2024_sub_ice_n90.0_s0.0_w-180.0_e-90.0.tif  N00W180.tif
mv gebco_2024_sub_ice_n90.0_s0.0_w-90.0_e0.0.tif     N00W090.tif
mv gebco_2024_sub_ice_n90.0_s0.0_w90.0_e180.0.tif    N00E090.tif
rm geotiff
rm GEBCO_Grid_Documentation.pdf
rm GEBCO_Grid_terms_of_use.pdf

cd ../..

# Configura OpenTopodata per usare il dataset GEBCO
cat <<EOT > config.yaml
datasets:
- name: gebco
  path: data/gebco/
  filename_tile_size: 90
EOT

sed -i 's/\b[Aa][Ss]\b/AS/' Dockerfile
sed -i 's/-it //' Makefile

make build

make run