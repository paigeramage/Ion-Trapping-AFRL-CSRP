#=========================================================================================#
#                PicoScope Automation Code to read Quad-Photodiode (PDQ80A)               #
#                                                                                         #
#                                 Written by: Gunnar Gott                                 #
#                                       11 June 2024                                      #
#                                                                                         #
#                                Modified by: Nick Kreidler                               #
#                                       14 July 2026                                      #
#                                                                                         #
# Purpose : Measure and analyze data off a PDQ80A using a 5444D PicoScope.                #
# Ch A = X-diff, Ch B = Y-diff, Ch C = SUM.                                               #
#                                                                                         #
# Please see the READ ME in the Beam Vibrations Folder of GitHub for instructions on what #
# software to develop, setup/parts, and how to run.                                       #
#=========================================================================================#

import ctypes
import numpy as np
from picosdk.ps5000a import ps5000a as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adc
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.signal import spectrogram, welch
from datetime import datetime
import time
import os

# playsound is optional flavor; don't let a missing file kill the run
try:
    from playsound import playsound  # USE playsound==1.2.2
except Exception:
    def playsound(*a, **k):
        pass

###################################
#      TEST   DOCUMENTATION       #
###################################
userTest = input("Type test name: ")
print("\n")

###################################
#          OSCOPE SETUP           #
###################################
chandle = ctypes.c_int16()
status = {}

resolution = ps.PS5000A_DEVICE_RESOLUTION["PS5000A_DR_12BIT"]
status["openunit"] = ps.ps5000aOpenUnit(ctypes.byref(chandle), None, resolution)

try:
    assert_pico_ok(status["openunit"])
except:  # PicoNotOkError
    powerStatus = status["openunit"]
    if powerStatus == 286:
        status["changePowerSource"] = ps.ps5000aChangePowerSource(chandle, powerStatus)
    elif powerStatus == 282:
        status["changePowerSource"] = ps.ps5000aChangePowerSource(chandle, powerStatus)
    else:
        raise
    assert_pico_ok(status["changePowerSource"])

enabled = 1
disabled = 0

coupling_type = ps.PS5000A_COUPLING['PS5000A_DC']
channel_range = ps.PS5000A_RANGE['PS5000A_100MV']   # all 3 channels share this range
analogue_offset = 0.0

for chName in ('A', 'B', 'C'):
    status["setCh" + chName] = ps.ps5000aSetChannel(
        chandle,
        ps.PS5000A_CHANNEL['PS5000A_CHANNEL_' + chName],
        enabled, coupling_type, channel_range, analogue_offset)
    assert_pico_ok(status["setCh" + chName])

###################################
#           SAMPLING              #
###################################
sizeOfOneBuffer = int(500e3)

timeInterval = 2    # decrease (or change units) for a higher sample rate
sampleInterval = ctypes.c_int32(timeInterval)
sampleUnits = ps.PS5000A_TIME_UNITS['PS5000A_US']

if sampleUnits == ps.PS5000A_TIME_UNITS['PS5000A_US']:
    timePrefixString, timePrefix, timeMult = "us", 1e-6, 1e3
if sampleUnits == ps.PS5000A_TIME_UNITS['PS5000A_NS']:
    timePrefixString, timePrefix, timeMult = "ns", 1e-9, 1
if sampleUnits == ps.PS5000A_TIME_UNITS['PS5000A_MS']:
    timePrefixString, timePrefix, timeMult = "ms", 1e-3, 1e6

testTime = sizeOfOneBuffer * timePrefix * timeInterval
print(f"Test time per buffer -> ~{testTime} sec")
timeTest = input("Enter test time multiplier (# of buffers): ")

numBuffersToCapture = int(timeTest)
totalSamples = sizeOfOneBuffer * numBuffersToCapture

maxPreTriggerSamples = 0
autoStopOn = 1

# Driver-registered buffers (one buffer's worth)
bufferAMax = np.zeros(shape=sizeOfOneBuffer, dtype=np.int16)
bufferBMax = np.zeros(shape=sizeOfOneBuffer, dtype=np.int16)
bufferCMax = np.zeros(shape=sizeOfOneBuffer, dtype=np.int16)

memory_segment = 0
ratio_mode = ps.PS5000A_RATIO_MODE['PS5000A_RATIO_MODE_NONE']

for chName, buf in (('A', bufferAMax), ('B', bufferBMax), ('C', bufferCMax)):
    status["setDataBuffers" + chName] = ps.ps5000aSetDataBuffers(
        chandle,
        ps.PS5000A_CHANNEL['PS5000A_CHANNEL_' + chName],
        buf.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
        None, sizeOfOneBuffer, memory_segment, ratio_mode)
    assert_pico_ok(status["setDataBuffers" + chName])

downsampleRatio = 1
status["runStreaming"] = ps.ps5000aRunStreaming(
    chandle, ctypes.byref(sampleInterval), sampleUnits,
    maxPreTriggerSamples, totalSamples, autoStopOn, downsampleRatio,
    ps.PS5000A_RATIO_MODE['PS5000A_RATIO_MODE_NONE'], sizeOfOneBuffer)
assert_pico_ok(status["runStreaming"])

actualSampleInterval = sampleInterval.value
actualSampleIntervalNs = actualSampleInterval * timeMult
print("Capturing at sample interval %s ns" % actualSampleIntervalNs)

# Big buffers to hold the full capture
bufferCompleteA = np.zeros(shape=totalSamples, dtype=np.int16)
bufferCompleteB = np.zeros(shape=totalSamples, dtype=np.int16)
bufferCompleteC = np.zeros(shape=totalSamples, dtype=np.int16)
nextSample = 0
autoStopOuter = False
wasCalledBack = False

def streaming_callback(handle, noOfSamples, startIndex, overflow,
                       triggerAt, triggered, autoStop, param):
    global nextSample, autoStopOuter, wasCalledBack
    wasCalledBack = True
    destEnd = nextSample + noOfSamples
    sourceEnd = startIndex + noOfSamples
    bufferCompleteA[nextSample:destEnd] = bufferAMax[startIndex:sourceEnd]
    bufferCompleteB[nextSample:destEnd] = bufferBMax[startIndex:sourceEnd]
    bufferCompleteC[nextSample:destEnd] = bufferCMax[startIndex:sourceEnd]
    nextSample += noOfSamples
    if autoStop:
        autoStopOuter = True

cFuncPtr = ps.StreamingReadyType(streaming_callback)

print("Fetching data from driver...")
try:
    playsound(r"C:\Users\Gunthar\Documents\picosdk-python-wrappers-master\romeScripts\Pig_death.mp3")
except Exception:
    pass
while nextSample < totalSamples and not autoStopOuter:
    wasCalledBack = False
    status["getStreamingLastestValues"] = ps.ps5000aGetStreamingLatestValues(chandle, cFuncPtr, None)
    if not wasCalledBack:
        time.sleep(0.01)
try:
    playsound(r"C:\Users\Gunthar\Documents\picosdk-python-wrappers-master\romeScripts\Zombie_idle3.mp3")
except Exception:
    pass
print("Done grabbing values.")

capturedSamples = nextSample   # may be < totalSamples if the driver stopped early

maxADC = ctypes.c_int16()
status["maximumValue"] = ps.ps5000aMaximumValue(chandle, ctypes.byref(maxADC))
assert_pico_ok(status["maximumValue"])

status["stop"] = ps.ps5000aStop(chandle)
assert_pico_ok(status["stop"])
print("O-Scope stopped")

numValues = ctypes.c_uint32()
status["noOfStreamingValue"] = ps.ps5000aNoOfStreamingValues(chandle, ctypes.byref(numValues))
print(f"Number of Samples -> {capturedSamples}")

# True sample rate straight from the (driver-confirmed) sample interval
fs = 1.0 / (actualSampleInterval * timePrefix)
sampleTime = (capturedSamples - 1) * actualSampleIntervalNs / 1e9
print(f"Time of sampling -> {sampleTime:.4f} sec")
print(f"Rate -> {fs:.1f} Sa/s")

status["close"] = ps.ps5000aCloseUnit(chandle)
assert_pico_ok(status["close"])
print(status)

###################################
#              MATH               #
###################################
# Trim to what was actually captured (prevents trailing zeros -> false SUM=0)
bufferCompleteA = bufferCompleteA[:capturedSamples]
bufferCompleteB = bufferCompleteB[:capturedSamples]
bufferCompleteC = bufferCompleteC[:capturedSamples]

# Time axis (named 't' so we don't clobber the 'time' module used above)
t = np.arange(capturedSamples) * actualSampleIntervalNs / 1e9

# Fast, vectorized ADC -> mV. (Mirrors picosdk's adc2mV ranges but ~1000x faster
# than its per-sample Python loop.) All 3 channels share `channel_range`.
channelInputRanges_mV = (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000)
range_mV = channelInputRanges_mV[channel_range]
conv = range_mV / maxADC.value                       # mV per ADC count

chA_mV = bufferCompleteA.astype(np.float64) * conv   # X-diff
chB_mV = bufferCompleteB.astype(np.float64) * conv   # Y-diff
chC_mV = bufferCompleteC.astype(np.float64) * conv   # SUM

# --- Diagnostics: SUM level and clipping check ---
fullScale = maxADC.value
clip = {ch: np.mean(np.abs(b) >= 0.99 * fullScale) * 100
        for ch, b in (('A', bufferCompleteA), ('B', bufferCompleteB), ('C', bufferCompleteC))}
print(f"SUM (Ch C): mean {chC_mV.mean():.2f} mV | min {chC_mV.min():.2f} | max {chC_mV.max():.2f}")
if max(clip.values()) > 0:
    print(f"WARNING: clipping A {clip['A']:.2f}%  B {clip['B']:.2f}%  C {clip['C']:.2f}% "
          f"-> raise channel_range or lower laser power")

# --- Normalized position: diff / SUM (dimensionless, power-independent) ---
# Guard divide-by-zero when the beam wanders off the detector (SUM ~ 0).
sumThreshold = 0.02 * abs(np.median(chC_mV))
valid = np.abs(chC_mV) > sumThreshold
if not np.all(valid):
    print(f"WARNING: {np.count_nonzero(~valid)} samples with SUM below threshold "
          f"(beam off detector?) -> NaN")
sum_safe = np.where(valid, chC_mV, np.nan)

# -1 on X flips to match lab/cartesian orientation; *100 -> percent of full sum
xAxisMovement = -100.0 * (chA_mV / sum_safe)   # X diff / SUM  [%]
yAxisMovement =  100.0 * (chB_mV / sum_safe)   # Y diff / SUM  [%]

# NaN-free, DC-removed copies for FFT-based analysis (spectrogram / PSD)
xForSpec = np.nan_to_num(xAxisMovement - np.nanmean(xAxisMovement), nan=0.0)
yForSpec = np.nan_to_num(yAxisMovement - np.nanmean(yAxisMovement), nan=0.0)

##################################
#          DATA   SAVING         #
# MUST UPDATE folder_path TO RUN #
##################################
folder_path = r'C:\Users\quantum\.vscode\Documents'
roundedTime = round(sampleTime)
folder_name = f'{userTest}_{roundedTime}_sec'
subFolderPath = os.path.join(folder_path, folder_name)
os.makedirs(subFolderPath, exist_ok=True)

full_path_npz = os.path.join(subFolderPath, folder_name)
np.savez(full_path_npz,
         time=t,
         chA_mV=chA_mV, chB_mV=chB_mV, chC_mV=chC_mV,
         xAxisMovement=xAxisMovement, yAxisMovement=yAxisMovement,
         buffA=bufferCompleteA, buffB=bufferCompleteB, buffC=bufferCompleteC,
         rangeCh=channel_range, maxADC=maxADC.value,
         actualSampleIntervalNs=actualSampleIntervalNs,
         actualSampleInterval=actualSampleInterval, timeMult=timeMult,
         fs=fs)
print("Saved npz...")

contMessage = input("Type 'p' to see plotted information, else type anything: ")
if contMessage == 'p':
    ###################################
    #            PLOTTING             #
    ###################################
    print("Plotting...")

    # ---- Fig 1: X / Y movement vs time ----
    fig1, axs1 = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True, sharex='col')
    axs1[0].plot(t, xAxisMovement, lw=0.6)
    axs1[0].set(ylabel='X diff / SUM [%]', xlabel='Time [sec]', title='X movement vs time')
    axs1[0].grid(True, which='both')
    axs1[1].plot(t, yAxisMovement, lw=0.6, color='tab:orange')
    axs1[1].set(ylabel='Y diff / SUM [%]', xlabel='Time [sec]', title='Y movement vs time')
    axs1[1].grid(True, which='both')
    for ax in axs1:
        ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
    fig1.savefig(os.path.join(subFolderPath, f'{folder_name}_time.png'))

    # ---- Fig 2: PSD (Welch) — the key vibration-analysis view ----
    nperseg = min(capturedSamples, int(fs))          # ~1 s segments -> ~1 Hz resolution
    fX, PxxX = welch(xForSpec, fs=fs, window='hann', nperseg=nperseg)
    fY, PxxY = welch(yForSpec, fs=fs, window='hann', nperseg=nperseg)

    fig3, axs3 = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True, sharey=True)
    axs3[0].semilogy(fX, np.sqrt(PxxX))
    axs3[0].set(xlabel='Freq [Hz]', ylabel='ASD [% / \u221AHz]', title='X spectrum (Welch PSD)')
    axs3[0].set_xlim(0, 5000)   # vibration band — widen up to fs/2 if you need more
    axs3[0].grid(True, which='both')
    axs3[1].semilogy(fY, np.sqrt(PxxY), color='tab:orange')
    axs3[1].set(xlabel='Freq [Hz]', title='Y spectrum (Welch PSD)')
    axs3[1].set_xlim(0, 5000)
    axs3[1].grid(True, which='both')
    fig3.savefig(os.path.join(subFolderPath, f'{folder_name}_psd.png'))

    # ---- Fig 3: spectrograms ----
    specNperseg = min(capturedSamples, 16384)        # trade freq vs time resolution here
    frequenciesX, timesX, Sxx_X = spectrogram(xForSpec, fs=fs, nperseg=specNperseg)
    frequenciesY, timesY, Sxx_Y = spectrogram(yForSpec, fs=fs, nperseg=specNperseg)
    print("Spectrogram generated...")

    fig2, axs2 = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True, sharex='col')
    im1 = axs2[0].pcolormesh(timesX, frequenciesX / 1e3,
                             10 * np.log10(Sxx_X + 1e-20), shading='gouraud', vmin=-100)
    axs2[0].set(ylim=(0, 5), ylabel='Freq [kHz]', xlabel='Time [sec]', title='X')  # adjust ylim
    fig2.colorbar(im1, ax=axs2[0], label='Intensity [dB]')

    im2 = axs2[1].pcolormesh(timesY, frequenciesY / 1e3,
                             10 * np.log10(Sxx_Y + 1e-20), shading='gouraud', vmin=-100)
    axs2[1].set(ylim=(0, 5), ylabel='Freq [kHz]', xlabel='Time [sec]', title='Y')
    fig2.colorbar(im2, ax=axs2[1], label='Intensity [dB]')

    fig2.savefig(os.path.join(subFolderPath, f'{folder_name}_spec.png'))
    print("Saved figures...")

    plt.show()

print("Finished...")