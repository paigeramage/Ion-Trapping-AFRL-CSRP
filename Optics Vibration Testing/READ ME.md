# Imaging Optics Vibration Testing
This analysis uses a Thorlabs TTL100-A telecentric lens and a Positive 1951 USAF resolution test target illuminated by a flashlight to 
determine how UAS mechanical vibrations affect the performance of an imaging system. The objective is to quantify optical capabilities,
image displacement, vibration blur, sharpness, contrast, and resolution degradation caused by vibrations in all three spatial directions.

The test target provides known high-contrast spatial features that can be tracked throughout a recorded image sequence. Motion 
perpendicular to the optical axis is measured primarily through X and Y image displacement, while vibration parallel to the optical 
axis (Z) is evaluated through changes in focus and image quality.

## Setup
The imaging system should consist of:
1. Thorlabs TTL100-A telecentric lens (https://www.thorlabs.com/item/TTL100-A)
2. Allied Vision 1800 U-1240m Camera (https://www.edmundoptics.com/p/allied-vision-alvium-1800-u-1240m-117-1222mp-c-mount-usb-31-monochrome-camera/44763/)
3. Positive 1951 USAF resolution test target (https://www.thorlabs.com/resolution-test-targets?tabName=Overview)
4. Fiber tip plugged into a 4.6 mW 635 laser box (use the Ch1 trimpot screw to adjust the laser power until it is able to focus without ressonance pattern)

You will need to download the following for the program to run properly:
1. Vimba X Viewer
2. cv2 (install with pip install cv2)

Define the coordinate system as:
X: Horizontal image-plane motion.
Y: Vertical image-plane motion.
Z: Motion along the optical axis (focus).

## Calibration

Before vibration testing, determine the image scale in: pixels/mm or mm/pixel
The known dimensions and spatial frequencies of the 1951 USAF target can be used for calibration.
Image displacement can then be converted from pixels into physical displacement: 

## Results Found
### Ground Testing
Using a Mitutoyo 20x M Plan APO Objective Lens:
- Highest resolvable USAF element	was group 7 element 6
- Each pixel was 316 um

Metric              |   Baseline Result
X max displacement  |   718 um  
Y max displacement  |   628 um  

### Powered Drone Testing
The illuminated fiber tip, used as a proxy for a single fluorescing trapped ion, remained within the microscope camera's field of view and focal distance throughout the vibration test. Motion was limited to cyclical oscillations induced by the drone motors, with no evidence of target loss or random displacement. The largest vibrational effects on imaging occured during the first 5 seconds on powering on the drone as motors went from off to low power. Once powered on, the increases in speed had minimal effects on the position of the fiber tip. We attribute most motion in the system to the insecure attachment method used to hold the fiber tip in frame. This demonstrated that the platform's vibration characteristics are compatible with sustained optical observation of a fluorescing ion in a quantum sensing imaging system. To view the images taken during this test, see 2026_Summer_Intern_Work/Drone Running 2/ in the RITQ UAS Project Google Drive. 

## Notes
- A baseline image sequence should be collected with the UAS completely powered off. This measurement establishes the optical and image-processing noise floor.
- Use Vimba to focus the image before running the automated bursts. This will ensure you have a quality baseline. The camera cannot be open/running in Vimba when running the automated script (close manual camera before running python).
- A short exposure time should be used when measuring instantaneous mechanical displacement. For the Allied Vision camera used, the minimum exposure is 22.602 us.
- The target can be used to test initial camera settings and once comfortable operating the camera, swap it out for a fiber tip. 
- !! Expect a change in the focal distance when alternating between the target and fiber tip. !! 

