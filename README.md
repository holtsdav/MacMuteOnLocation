# MacMuteOnLocation

> **Note:** This application was created heavily with AI assistance, leveraging modern AI tools to accelerate development and ensure best practices.

MacMuteOnLocation is a macOS menu bar application that automatically mutes your microphone when you're at specific locations. Perfect for maintaining privacy during work-from-home scenarios or when you're in sensitive locations.

## Features

- 🎤 **Automatic Microphone Control**: Mutes/unmutes your microphone based on your current location
- 📍 **Location-Based Triggers**: Set specific locations where you want your microphone to be automatically muted
- 🔒 **Privacy-Focused**: All location data is stored locally on your device
- 🖥️ **Menu Bar Integration**: Clean, minimal interface that lives in your macOS menu bar
- ⚡ **Lightweight**: Minimal system resource usage
- 🎯 **Template Icon**: Automatically adapts to light/dark mode
- 🔧 **Configurable**: Customizable location radius and check intervals
- 🚀 **Launch at Login**: Optional automatic startup when you log in to macOS

## Requirements

- macOS 10.14 (Mojave) or later
- Location Services enabled
- Microphone access permission

## Installation

### Option 1: Download Pre-built App (Recommended)

1. Download the latest release from the [Releases](../../releases) page
2. Unzip the downloaded file
3. Move `MacMuteOnLocation.app` to your Applications folder
4. Right-click the app and select "Open" (required for first launch due to macOS security)

### Option 2: Build from Source

#### Prerequisites

- Python 3.8 or later
- Xcode Command Line Tools: `xcode-select --install`

#### Build Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/MacMuteOnLocation.git
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

- **Location Services**: To determine your current location
- **Microphone Access**: To control microphone mute/unmute functionality

All permissions are requested on first launch and can be managed in System Preferences > Security & Privacy.

## Privacy

- All location data is stored locally on your device
- No data is transmitted to external servers
- Location tracking only occurs when the app is running
- You can delete all stored locations at any time

## Development

### Project Structure

```
MacMuteOnLocation/
├── main.py                 # Main application entry point
├── setup.py               # py2app build configuration
├── build_app.sh           # Build script
├── requirements.txt       # Python dependencies
├── app_icon.icns         # Application icon
├── icon.iconset/         # Icon source files
├── location_dark.png     # Menu bar icon
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

### Dependencies

- **rumps**: Menu bar application framework
- **pyobjc**: Python-Objective-C bridge for macOS APIs
- **py2app**: Python to macOS app bundler
- **jaraco.text**: Text processing utilities

### Building Icons

To rebuild the app icon from the iconset:

```bash
iconutil -c icns icon.iconset
mv icon.icns app_icon.icns
```

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

### Microphone Not Muting
- Check microphone permissions in System Preferences > Security & Privacy
- Verify your microphone is working in other applications
- Restart the app if issues persist

### Build Issues

#### Carbon Framework Error
If you encounter Carbon framework loading issues:
- The current setup.py configuration excludes Carbon framework
- Ensure `argv_emulation=False` in py2app options

#### Missing Dependencies
If you get `ModuleNotFoundError` for jaraco.text:
```bash
pip install jaraco.text
```

## Technical Notes

### Resolved Issues

1. **Carbon Framework Loading**: Disabled `argv_emulation` and excluded Carbon framework to prevent compatibility issues on modern macOS
2. **Missing Dependencies**: Added jaraco.text and related packages to setup.py includes
3. **Icon Configuration**: Properly configured app icon in both py2app options and plist settings

### macOS Compatibility

- Tested on macOS 10.14+
- Uses modern Core Location APIs
- Follows macOS security model for location and microphone access

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -am 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [rumps](https://github.com/jaredks/rumps) for menu bar integration
- Uses macOS Core Location framework for location services
- Icon design inspired by macOS Human Interface Guidelines
- Developed with AI assistance for rapid prototyping and best practices

## Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page for existing solutions
2. Create a new issue with detailed information about your problem
3. Include your macOS version and any relevant error messages

---

**Note**: This app is designed for personal use and privacy. Always ensure you comply with local laws and regulations regarding location tracking and microphone usage.