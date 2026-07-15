#=========================================================================================#
#                    Automated Camera Bursts for Vibrations Testing                       #
#                          Using an Allied Vision 1800 u1240m                             #
#                                                                                         #
#                             Written by: Paige K. Ramage                                 #
#                                       June 2026                                         #
#                                                                                         #
# This program can be used to automate multiple bursts of any number of images with any   #
# time variation between bursts. It uses the camera settings with a hardware minimum of   #
# 22.206 us exposure time for the quickest photo bursts capable. This program saves all   #
# images from each burst into individual folders within the main folder of the test.      #
# These are all saved inside the larger images/ folder as defined in line 22.             #
#=========================================================================================#

from vmbpy import *             #library for camera
import cv2                      #library for photo saving stuff
import time                     #for exposure and burst delay
import os                       #idk... this was vibe code edition
from datetime import datetime   #used to add timestamps to photo names

# !!!  CHANGE THE NAME OF SAVE_FOLDER FOR EACH TEST  !!!
SAVE_FOLDER = "images/testing code" 
os.makedirs(SAVE_FOLDER, exist_ok=True) #ensures SAVE_FOLDER exists otherwise creates it

# CONFIG
EXPOSURE_US = 2             # 2 ms (200 required for 100 Hz) but I made faster-ish
BURSTS = 5                  # number of bursts per test
IMAGES_PER_BURST = 20       # number of images in each burst
FRAME_INTERVAL = 0.02       # 200 Hz = 20 ms
BURST_GAP = 10              # int num of seconds per interval btwn bursts
DELAY_START = 0             # int num of seconds between program run and photo initiation

def main():

    with VmbSystem.get_instance() as vmb:
        cam = vmb.get_all_cameras()[0]

        with cam:
            print("Camera:", cam.get_name())
            if DELAY_START > 0:
                print(f"Waiting {DELAY_START} seconds...")
                time.sleep(DELAY_START)

            # Set exposure
            cam.ExposureTime = EXPOSURE_US
            #cam.PixelFormat.set("Mono8")

            #Initiates Bursts
            for burst in range(BURSTS):
                print(f"\n--- BURST {burst+1}/{BURSTS} ---")

                # Create a folder for this burst named Burst_#
                burst_folder = os.path.join(SAVE_FOLDER, f"Burst_{burst+1}")
                os.makedirs(burst_folder, exist_ok=True)

                for i in range(IMAGES_PER_BURST):
                    frame = cam.get_frame(timeout_ms=3000)
                    img = frame.as_numpy_ndarray()

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = os.path.join(
                        burst_folder,
                        f"img_{i+1:02d}_{timestamp}.png" 
                    )

                    cv2.imwrite(filename, img)
                    print("Saved:", filename)

                    #time.sleep(FRAME_INTERVAL) commented out this line for maximum speed

                if burst < BURSTS - 1:
                    print(f"Waiting {BURST_GAP} seconds...")
                    time.sleep(BURST_GAP)

if __name__ == "__main__":
    main()
