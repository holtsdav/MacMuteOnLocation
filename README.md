# MacMuteOnLocation

MacMuteOnLocation is a lightweight macOS menu bar application that automatically mutes your Mac's microphone and speakers when you arrive at specific locations. 

Built natively for macOS using Python, it leverages Apple's Core Location framework for highly efficient, battery-friendly tracking without needing continuous GPS polling.

## Features

- 🔇 **Automatic Muting**: Mutes/unmutes your Mac based on your physical location.
- 📍 **Location Triggers**: Set specific locations (like the Office, a Library, or a Cafe) where your Mac should automatically mute itself.
- 💾 **Status Persistence**: Remembers the mute state and saved locations between launches.
- 🔒 **Privacy-Focused**: All location data is stored strictly locally on your device. No cloud sync, no tracking.
- ⚡ **Battery Friendly**: Configurable check intervals and wake-up scanning only.
- 🚀 **1-Click Auto-Start**: Built-in toggle to launch automatically when you log in.
- 🔄 **Auto-Updater**: Seamlessly download and install new updates directly from the menu bar.

## Requirements

- macOS 10.14 (Mojave) or later (Tested on Apple Silicon M-Series)
- Location Services enabled

## Installation (Important)

Because this application is open-source and not signed with a paid Apple Developer Account, macOS's Gatekeeper will quarantine the app and may claim the file is "damaged" upon first launch. 

Please follow these exact steps to install:

1. Download the latest `.zip` release from the [Releases](https://github.com/holtsdav/MacMuteOnLocation/releases) page.
2. Unzip the file.
3. Move `MacMuteOnLocation.app` into your **Applications** folder.
4. Open your Terminal and paste the following command to remove the Apple quarantine flag (requires your Mac admin password):
   ```bash
   sudo xattr -rd com.apple.quarantine /Applications/MacMuteOnLocation.app
   ```
5. Launch the app from your Applications folder! 

*(Note: You will only need to do this command on your very first install. Future updates handled by the built-in Auto-Updater will not require Terminal commands!)*

## Usage

1. **Permissions**: On first launch, macOS will prompt you to grant Location and Microphone permissions. Allow these so the app can function.
2. **Auto-Start**: You will be prompted to enable Auto-Start at login. You can toggle this anytime from the menu bar.
3. **Add Locations**: Click the menu bar icon and select **"🎯 Target Locations"** -> **"Add Current Location"** to save your current position as a mute zone.
4. **Operation**: The app will automatically mute your Mac when you enter a saved location and unmute when you leave.

## Building from Source

If you prefer to compile the application yourself:

1. Clone the repository and navigate into the directory:
   ```bash
   git clone https://github.com/holtsdav/MacMuteOnLocation.git
   cd MacMuteOnLocation
   ```
2. Set up a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Build the macOS App Bundle using GitHub Actions or `py2app` locally:
   ```bash
   python setup.py py2app
   ```
4. The compiled application will be located in the `dist/` directory.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License. You are free to use, modify, and distribute this software for non-commercial purposes, provided you give appropriate credit to the original author. See the [LICENSE](LICENSE) file for details.
