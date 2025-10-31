# Adhan Audio Asset

## Required File

This directory should contain an `adhan.mp3` file for voice channel playback.

## How to Add the Adhan Audio

1. **Download or Record**: Obtain a short Adhan (call to prayer) audio recording in MP3 format
   - Recommended length: 1-3 minutes
   - Format: MP3, 128kbps or higher

2. **Place the File**: Save the file as `assets/adhan.mp3`

3. **Verify**: The file should be located at:
   ```
   Athan/
   └── assets/
       └── adhan.mp3
   ```

## Sources for Adhan Audio

You can find free Adhan recordings from various sources:
- Public domain Islamic audio archives
- Creative Commons licensed recordings
- Record your own with proper equipment

## Important Notes

- Ensure the audio file is licensed for use in your deployment
- The bot will check for this file when `/adhan_voice` is called
- If the file is missing, the command will return a helpful error message
- FFmpeg must be installed on the system for playback to work

## Testing

To test voice playback:
1. Join a voice channel in Discord
2. Run `/adhan_voice` in a text channel
3. The bot will join your voice channel and play the Adhan

