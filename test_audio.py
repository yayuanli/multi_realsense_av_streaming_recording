#!/usr/bin/env python3
"""Minimal audio recording test script with device selection"""

import sounddevice as sd
import wave
import numpy as np

def list_audio_devices():
    """List all available audio devices"""
    devices = sd.query_devices()
    print("\nAvailable audio devices:")
    print("-" * 50)
    for i, device in enumerate(devices):
        device_type = []
        if device['max_inputs'] > 0:
            device_type.append("INPUT")
        if device['max_outputs'] > 0:
            device_type.append("OUTPUT")
        
        print(f"{i:2d}: {device['name']}")
        print(f"    Type: {'/'.join(device_type)}")
        print(f"    Channels: IN={device['max_inputs']}, OUT={device['max_outputs']}")
        print(f"    Sample Rate: {device['default_samplerate']:.0f} Hz")
        print()
    
    return devices

def choose_input_device():
    """Let user choose input device"""
    devices = list_audio_devices()
    
    # Find input devices
    input_devices = []
    for i, device in enumerate(devices):
        if device['max_inputs'] > 0:
            input_devices.append(i)
    
    if not input_devices:
        print("No input devices found!")
        return None
    
    print(f"Input devices available: {input_devices}")
    print(f"Default input device: {sd.default.device[0]}")
    
    while True:
        try:
            choice = input(f"\nChoose input device (0-{len(devices)-1}) or press Enter for default: ").strip()
            if choice == "":
                return sd.default.device[0]
            
            device_id = int(choice)
            if device_id in input_devices:
                return device_id
            else:
                print(f"Device {device_id} is not an input device. Choose from: {input_devices}")
        except ValueError:
            print("Please enter a valid number")

def test_audio_recording(device_id=None, duration=5, filename="test_audio.wav"):
    """Record audio for specified duration and save to file"""
    
    sample_rate = 44100
    channels = 2
    
    print(f"\nRecording {duration} seconds of audio...")
    if device_id is not None:
        device_info = sd.query_devices(device_id)
        print(f"Using device: {device_info['name']}")
        
        # Adjust channels if device doesn't support stereo
        max_channels = device_info['max_inputs']
        if max_channels < channels:
            channels = max_channels
            print(f"Device only supports {channels} channel(s), adjusting...")
    
    try:
        # Record audio
        audio_data = sd.rec(int(duration * sample_rate), 
                           samplerate=sample_rate, 
                           channels=channels, 
                           dtype=np.float32,
                           device=device_id)
        
        print("Recording... (make some noise!)")
        sd.wait()
        
        max_amplitude = np.max(np.abs(audio_data))
        print(f"Recording complete. Max amplitude: {max_amplitude:.3f}")
        
        if max_amplitude < 0.001:
            print("WARNING: Very low audio level detected. Check microphone and volume settings.")
        
        # Save as WAV file
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Convert float32 to int16
            audio_int16 = (audio_data * 32767).astype(np.int16)
            wav_file.writeframes(audio_int16.tobytes())
        
        print(f"Audio saved to: {filename}")
        
        # Test playback
        print("\nTesting playback...")
        try:
            sd.play(audio_data, sample_rate)
            sd.wait()
            print("Playback complete")
        except Exception as e:
            print(f"Playback error: {e}")
            
    except Exception as e:
        print(f"Recording error: {e}")

if __name__ == "__main__":
    print("Audio Recording Test")
    print("=" * 50)
    
    device_id = choose_input_device()
    if device_id is not None:
        test_audio_recording(device_id)