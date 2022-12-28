import librosa
import librosa.display
import numpy as np
import IPython.display as ipd
from matplotlib import cm
import matplotlib.pyplot as plt
from colorspacious import cspace_converter

audio_path = '210901_project/sound.wav'
ipd.Audio(audio_path)

y, sr = librosa.load(audio_path, sr=16000)

# def get_stft(sample_sounds):
#     return librosa.stft(sample_sounds)

# def draw_stft(sample_sounds, ylim=(None, None)):
#     plt.figure(figsize=(12,6))
#     librosa.display.specshow(np.abs(get_stft(sample_sounds)), 
#                              y_axis='hz', x_axis='s')
#     plt.ylim(ylim); plt.grid(); plt.show()
        
# def get_chroma(sample_sounds, sr):
#     return librosa.feature.chroma_stft(S=np.abs(get_stft(sample_sounds)), 
#                                        sr=sr)

# def draw_chroma(sample_sounds, sr):
#     plt.figure(figsize=(12,6))
#     librosa.display.specshow(get_chroma(sample_sounds, sr), 
#                              y_axis='chroma', x_axis='time')
#     plt.grid(); plt.show()


print('sr:', sr, ', audio shape:', y.shape)
print('length:', y.shape[0]/float(sr), 'secs')

# plt.figure(figsize = (10,5))
# librosa.display.waveshow(y, sr=sr)
# plt.ylabel("Amplitude")
# plt.show()

plt.figure()
librosa.display.waveshow(y, sr, alpha=0.5)
plt.xlabel("Time (s)")
plt.ylabel("Amplitude")
plt.title("Waveform")
plt.show()

fft = np.fft.fft(y)

magnitude = np.abs(fft) 
frequency = np.linspace(0,sr,len(magnitude))

left_spectrum = magnitude[:int(len(magnitude) / 2)]
left_frequency = frequency[:int(len(frequency) / 2)]

plt.figure(figsize = (10,5))
plt.plot(left_frequency, left_spectrum)
plt.xlabel("Frequency")
plt.ylabel("Magnitude")
plt.title("Power spectrum")

plt.show()

n_fft = 2048 
hop_length = 512 
stft = librosa.stft(y, n_fft = n_fft, hop_length = hop_length)
spectrogram = np.abs(stft)
# print("Spectogram :\n", spectrogram)
# plt.figure(figsize = (10,5))
# librosa.display.specshow(spectrogram, sr=sr, hop_length=hop_length)
# plt.xlabel("Time")
# plt.ylabel("Frequency")
# plt.plasma()
# plt.show()

log_spectrogram = librosa.amplitude_to_db(spectrogram)


plt.figure(figsize = (10,5))
librosa.display.specshow(log_spectrogram, sr=sr, hop_length=hop_length, x_axis='time', y_axis='log')
plt.xlabel("Time")
plt.ylabel("Frequency")
plt.colorbar(format="%+2.0f dB")
plt.title("Spectrogram (dB)")
plt.show()

mfcc = librosa.feature.mfcc(y, sr=16000, n_mfcc=20, n_fft=n_fft, hop_length=hop_length)

# print("MFCC Shape: ", mfcc.shape)
# print("MFCC: \n", mfcc)

# plt.figure(figsize = (10,5))
# librosa.display.specshow(mfcc, sr=16000, hop_length=hop_length, x_axis='time')
# plt.xlabel("Time")
# plt.ylabel("Frequency")
# plt.colorbar(format='%+2.0f dB')
# plt.show()

# stft_result = librosa.stft(y, n_fft=4096, win_length = 4096, hop_length=256)
# D = np.abs(stft_result)
# S_dB = librosa.power_to_db(D, ref=np.max)
# librosa.display.specshow(S_dB, sr=sr, hop_length = 1024, y_axis='linear', x_axis='time', cmap = cm.jet)
# plt.colorbar(format='%2.0f dB')
# plt.show()


plt.figure(figsize = (10,5))
librosa.feature.spectral_contrast(y=None, sr=22050, S=None, n_fft=2048, hop_length=512, win_length=None, window='hann', center=True, pad_mode='constant', freq=None, fmin=200.0, n_bands=6, quantile=0.02, linear=False)
plt.xlabel("Time")
plt.ylabel("Frequency")
plt.colorbar(format="%+2.0f dB")
plt.title("Spectrogram (dB)")
plt.show()
