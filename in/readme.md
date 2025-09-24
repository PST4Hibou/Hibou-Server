## Directory Structure

This directory structure is used to read audio files from the disk for debugging purposes.

The audio files must be organized per channel in separate folders. Each channel folder contains the WAV files for that channel.

### Example

If you have 2 channels (`ch0` and `ch1`), the folder structure should look like this:


```shell
in/ # You are here
├── ch_0/
│ ├── file_0.wav
│ ├── file_1.wav
│ └── ...
├── ch_1/
│ ├── file_0.wav
│ ├── file_1.wav
│ └── ...
```


- `in/` → the folder you pass as `folder_path` to `FileAudioSource`.
- `ch_0`, `ch_1`, … → subfolders for each channel. The names are constructed as `{channel_prefix}{index}`, e.g., `"ch_0"`, `"ch_1"`.
- Each subfolder must contain one or more `.wav` files. Files are read in **sorted order**.

---

## Requirements for WAV Files

- **Sample rate**: All WAV files must have the same sample rate only 48kHz is supported for now.
- **File extension**: All files must have the `.wav` extension.  
- **Channels**: Each file should have the same number of channels (mono/stereo) for consistency.  
- **Duration**: Files for each channel should ideally have the same number of frames for proper synchronization.

The program will raise errors if any of these conditions are not met.

