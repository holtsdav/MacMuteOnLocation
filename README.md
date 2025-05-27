# MacMuteOnLocation

> **Note:** This application was created heavily with AI assistance.

MacMuteOnLocation is a macOS menu bar application that automatically mutes your Mac's volume when you're at specific locations.

## Important Install Instructions
**Apple will say the App is Damaged if you don't follow Step 3**

1. Unzip the File
2. Move the .app File to the Applications Folder
3. Paste this into your Terminal (**Required** Since i don't have an Apple Developer Account)
   `sudo xattr -rd com.apple.quarantine /Applications/MacMuteOnLocation.app`  _(Admin Permission Required)_
5. Enjoy
   
## Features

- 🔇 **Automatic Volume Control**: Mutes/unmutes your Mac's volume based on your current location.
- 📍 **Location-Based Triggers**: Set specific locations where you want your Mac's volume to be automatically muted.
- 💾 **Status Persistence**: Remembers the mute state and saved locations between launches using a local JSON file.
- 🔒 **Privacy-Focused**: All location data and settings are stored locally on your device.
- 🖥️ **Menu Bar Integration**: Clean, minimal interface that lives in your macOS menu bar.
- ⚡ **Lightweight**: Minimal system resource usage.
- 🔧 **Configurable**: Customizable location radius and check intervals.
- 🚀 **Launch at Login**: Requires *manual* setup via System Settings or Finder to launch automatically at login.

## Requirements

- Not Sure if Intel Macs are supported
- macOS 10.14 (Mojave) or later
- Location Services enabled

## Installation

### Option 1: Download Pre-built App (Recommended)

1. Download the latest release from the [Releases](https://github.com/holtsdav/MacMuteOnLocation/releases) page
2. Unzip the downloaded file
3. Move `MacMuteOnLocation.app` to your Applications folder
4. Right-click the app and select "Open" (required for first launch due to macOS security)

### Option 2: Build from Source (Not checked the Readme might include Errors)

#### Prerequisites

- Python 3.8 or later
- Xcode Command Line Tools: `xcode-select --install` (may not be required)
- py2app: `pip install py2app` (or will be auto-installed during build)

#### Build Steps (Not testet)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/holtsdav/MacMuteOnLocation.git
   cd MacMuteOnLocation
   ```

2. **Set up virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Build the app**:
   ```bash
   ./build_app.sh
   ```

   Or manually:
   ```bash
   python setup.py py2app
   ```

5. **Run the app**:
   ```bash
   open dist/MacMuteOnLocation.app
   ```

## Usage

1. **First Launch**: Grant location and microphone permissions when prompted
2. **Add Locations**: Click the menu bar icon and select "Add Current Location" to save your current position as a mute zone
3. **Manage Locations**: Use the menu to view, edit, or remove saved locations
4. **Automatic Operation**: The app will automatically mute your microphone when you enter a saved location and unmute when you leave

## Menu Options

- **Add Current Location**: Save your current location as a mute zone
- **Show Locations**: View all saved locations
- **Check Interval**: Configure how frequently the app checks your location
- **Launch at Login**: Enable/disable automatic startup when you log in
- **Quit**: Exit the application

## Permissions

The app requires the following permissions:

- **Location Services**: To determine your current location.
- **System Events/Accessibility**: May be required depending on the method used to control system volume.

Permissions are typically requested on first launch and can be managed in System Settings > Privacy & Security.

## Privacy

- All location data is stored locally on your device
- No data is transmitted to external servers
- Location tracking only occurs when the app is running
- You can delete all stored locations at any time


### Project Structure

```
MacMuteOnLocation/
├── main.py                 # Main application entry point
├── setup.py                # py2app build configuration
├── build_app.sh            # Build script
├── requirements.txt        # Python dependencies
├── app_icon.icns           # Application icon
├── icon.iconset/           # Icon source files
├── location_dark.png       # Menu bar icon
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

### Dependencies

- **rumps**: Menu bar application framework
- **pyobjc-framework-CoreLocation**: Python bridge for Core Location services
- **pyobjc-framework-Foundation**: Core Python-Objective-C bridge for macOS APIs


### Development Setup

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd MacMuteOnLocation
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run in development mode**:
   ```bash
   python main.py
   ```

3. **Build for distribution**:
   ```bash
   ./build_app.sh
   ```

## Troubleshooting

### App Won't Launch
- Ensure you've granted all required permissions
- Try right-clicking and selecting "Open" instead of double-clicking
- Check Console.app for error messages

### Location Not Detected
- Verify Location Services is enabled in System Preferences
- Ensure the app has location permission
- Try moving to a different location and back



### macOS Compatibility

- Tested on macOS 10.14+
- Uses modern Core Location APIs
- Follows macOS security model for location
  
## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -am 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.
You are free to use, modify, and distribute this software for non-commercial purposes, provided you give appropriate credit to the original author. - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [rumps](https://github.com/jaredks/rumps) for menu bar integration
- Uses macOS Core Location framework for location services
- Uses AppKit framework for system integration and appearance detection
- Uses subprocess module for system volume control via osascript
- Icon design inspired by macOS Human Interface Guidelines
- Developed with AI assistance for rapid prototyping and best practices

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/holtsdav/MacMuteOnLocation/issues) page for existing solutions
2. Create a new issue with detailed information about your problem
3. Include your macOS version and any relevant error messages

---

**Note**: This app is designed for personal use and privacy. Always ensure you comply with local laws and regulations regarding location tracking usage.
