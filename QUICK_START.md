# YouTube Shorts Uploader - Quick Start Guide

## 1. Setup (Initial Setup Only)

### Windows
```batch
setup.bat
```

### Linux/Mac/WSL
```bash
./setup.sh
```

This will:
- Create a virtual environment
- Install all dependencies
- Create necessary directories
- Check for ffmpeg and optionally install it

**Note:** If ffmpeg is not installed, the setup script will:
- **Windows**: Offer to install via winget (Windows 10/11 standard), then Chocolatey if available
- **Linux**: Offer to install via apt-get or dnf
- **macOS**: Offer to install via Homebrew

### Installing ffmpeg manually (if needed)

**Windows - Recommended methods (in order):**

1. **winget (Built-in for Windows 10/11):**
```batch
winget install -e --id Gyan.FFmpeg
```

2. **Portable version (No PATH needed):**
```batch
install_ffmpeg_portable.bat
```

3. **Chocolatey:**
```batch
choco install ffmpeg
```

**Alternative:** You can skip video validation with `--skip-validation` if ffmpeg is not installed.

## 2. Authenticate with YouTube

### Windows
```batch
run.bat auth --show-info
```

### Linux/Mac
```bash
./run.sh auth --show-info
```

A browser will open for you to:
1. Select your Google account
2. Grant permissions for YouTube upload
3. Complete authentication

After successful authentication, a `token.json` file will be created.

## 3. Upload a Video

### Single Video Upload

**Windows:**
```batch
run.bat upload shorts_videos\video.mp4 -t "My First Short" -d "Description here"
```

**Linux/Mac:**
```bash
./run.sh upload shorts_videos/video.mp4 -t "My First Short" -d "Description here"
```

### Batch Upload (Multiple Videos)

**Windows:**
```batch
run.bat batch -d shorts_videos -i 30 --save-history
```

**Linux/Mac:**
```bash
./run.sh batch -d shorts_videos -i 30 --save-history
```

This will upload all MP4 files in the `shorts_videos` directory with 30 minutes interval.

## 4. Check API Quota

```batch
run.bat quota
```

## Common Options

### Upload Options
- `-t, --title` : Video title (required)
- `-d, --description` : Video description
- `--tags` : Tags (comma-separated)
- `-p, --privacy` : Privacy status (public/private/unlisted)
- `--force` : Force upload even if validation fails

### Examples

**Private Upload:**
```batch
run.bat upload video.mp4 -t "Test Video" -p private
```

**With Tags:**
```batch
run.bat upload video.mp4 -t "Tutorial" --tags "Shorts,Tutorial,Python"
```

**Validate Before Upload:**
```batch
run.bat validate video.mp4
```

## Important Notes

### API Quota Limits
- Daily limit: 10,000 units
- One video upload: 1,600 units
- Maximum uploads per day: ~6 videos

### YouTube Shorts Requirements
- Aspect ratio: 9:16 (vertical) or 1:1 (square)
- Duration: Up to 180 seconds (3 minutes)
- Resolution: 1920x1080 recommended
- Format: MP4 or MOV

### Windows Task Scheduler (For Automated Daily Uploads)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., Daily at 10:00 AM)
4. Action: Start a program
   - Program: `cmd.exe`
   - Arguments: `/c cd /d "C:\path\to\YouTubeShortsUploader" && run.bat batch -d shorts_videos`
5. Test the task

## Troubleshooting

### Authentication Fails
- Delete `token.json` and try again
- Check client_secret file is in the project root
- Verify OAuth scopes in Google Cloud Console

### Upload Fails
- Check your video meets YouTube Shorts requirements
- Verify API quota is not exceeded
- Ensure internet connection is stable

### For WSL Users
- Authentication requires a browser, so you may need to copy the URL manually
- Consider running the tool on Windows native for better compatibility

## Need Help?

See the full documentation in [README.md](README.md) for detailed information.
