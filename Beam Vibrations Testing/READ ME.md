# Fiber to Beam Testing Experiment
This experiment uses a standard beam to determine how the beam responds as a result of drone vibrations in its ability to focus on a specific point in space when moved closer to the drone from underneath. 

## Setup
This experiment requires Python 2 or 3 to be installed on the device that is running the programs.

The following software will also need to be installed:
1. DataRay (BladeCam2-XHR)- https://dataray.com/resources/downloads
2. PicoScope7 (PicoScope 5444D MSO)- https://www.picotech.com/downloads
3. picoSDK - Under the same link as PicoScope7 (follow directions online to install sdk after download)
4. picoSDK Wrapper - https://github.com/picotech/picosdk-python-wrappers

You will need to install the following packages using pip (full like would be 'pip install --upgrade PACKAGE'):
1. ctypes
2. numpy
3. matplotlib
4. scipy

Additionally, the following git command(s) need to be run through the command line if you plan to push results to github and use LFS:
1. git lfs install
2. git lfs track "*.npz"
3. git add .gitattributes
4. git lfs migrate import --include="*.npz
5. git commit -m "LFS"
6. git push

## Helpful Links
- https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=4400
- https://stackoverflow.com/questions/35518688/git-lfs-refused-to-track-my-large-files-properly-until-i-did-the-following
- https://github.com/gunnargott/copterScripts

## Notes
- The .npz files that this script creates can be used to process data previously collected after the fact. Ex: to generate new/different graphs.
- to allign the Picoscope using the PicoScope7 software, turn Channels A-C on manual mode +-500mV. Then, allign the scope so that Channels A & B are at roughly 0mV and channel C is at roughly 400mV. It can be helpful to zoom in along the x-axis to see less noise. Channel A represents X position, B represents Y position, and C represents total voltage seen by the scope.
- To power the laser with the power supply, set +25V AND -25V to ~7V. There is a current regulator inside of the light source so it can handle a variety of currents supplied.
- The laser we are using has WL=635nm, the lens we are using has FL=50mm.
- You can hardwire connect to the picoscope using a USB cable, connect to the UAS over the network.
- Zach should be up to date about the motivation behind each of the graphs we chose to generate, if not, feel free to generate different ones from the .npz file or edit this script.
