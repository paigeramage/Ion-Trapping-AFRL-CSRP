import ids_peak.ids_peak as ids_peak
import ids_peak_ipl
import numpy as np
import cv2
import os
import time
from datetime import datetime

SAVE_FOLDER = "images/Drone Running 3"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# CONFIG
EXPOSURE_US = 8.99
BURSTS = 5
IMAGES_PER_BURST = 20
BURST_GAP = 8
DELAY_START = 0


def open_camera():

    ids_peak.Library.Initialize()

    device_manager = ids_peak.DeviceManager.Instance()
    device_manager.Update()

    if device_manager.Devices().empty():
        raise RuntimeError("No IDS camera found.")

    device = device_manager.Devices()[0].OpenDevice(
        ids_peak.DeviceAccessType_Control
    )

    datastream = device.DataStreams()[0].OpenDataStream()

    nodemap = device.RemoteDevice().NodeMaps()[0]

    return device, datastream, nodemap


def configure_camera(datastream, nodemap):

    nodemap.FindNode("ExposureTime").SetValue(EXPOSURE_US)

    payload_size = nodemap.FindNode("PayloadSize").Value()

    num_buffers = datastream.NumBuffersAnnouncedMinRequired()

    for _ in range(num_buffers):
        buffer = datastream.AllocAndAnnounceBuffer(payload_size)
        datastream.QueueBuffer(buffer)

    datastream.StartAcquisition()

    nodemap.FindNode("AcquisitionStart").Execute()


from ids_peak_ipl import ids_peak_ipl

def grab_image(datastream):

    buffer = datastream.WaitForFinishedBuffer(5000)

    width = buffer.Width()
    height = buffer.Height()

    img = None

    try:
        image = ids_peak_ipl.Image.CreateFromSizeAndBuffer(
            buffer.PixelFormat(),
            buffer.BasePtr(),
            buffer.Size(),
            width,
            height
        )

        # Convert IDS image to Mono8
        image = image.ConvertTo(ids_peak_ipl.PixelFormatName_Mono8)

        # Use numpy array from IDS IPL
        img = image.get_numpy_1D().reshape(height, width)

        # Detach from IDS memory
        img = img.copy()

    finally:
        # Always return buffer
        datastream.QueueBuffer(buffer)

    return img

def main():

    device, datastream, nodemap = open_camera()

    configure_camera(datastream, nodemap)

    if DELAY_START > 0:
        time.sleep(DELAY_START)

    for burst in range(BURSTS):

        print(f"BURST {burst+1}/{BURSTS}\n")

        burst_folder = os.path.join(
            SAVE_FOLDER,
            f"Burst_{burst+1}"
        )

        os.makedirs(burst_folder, exist_ok=True)

        for i in range(IMAGES_PER_BURST):

            img = grab_image(datastream)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

            filename = os.path.join(
                burst_folder,
                f"img_{i+1:02d}_{timestamp}.png"
            )

            success = cv2.imwrite(filename, img)

            if success:
                print("Saved:", filename)
            else:
                print("FAILED:", filename)
                print("Exists folder:", os.path.exists(burst_folder))
                print("Writable:", os.access(burst_folder, os.W_OK))
                print("Shape:", img.shape)
                print("dtype:", img.dtype)

        if burst < BURSTS - 1:
            print(f"Waiting for {BURST_GAP} seconds\n\n")
            time.sleep(BURST_GAP)

    nodemap.FindNode("AcquisitionStop").Execute()
    datastream.StopAcquisition()
    ids_peak.Library.Close()


if __name__ == "__main__":
    main()