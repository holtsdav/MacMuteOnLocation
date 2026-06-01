import re
from setuptools import setup

# Extract version from main.py
with open('main.py', 'r') as f:
    match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE)
    version = match.group(1) if match else '0.0.1'

import os

# Get all png files in icons directory
icon_files = [os.path.join('icons', f) for f in os.listdir('icons') if f.endswith('.png')]

APP = ['main.py']
DATA_FILES = [('', ['location_dark.png']), ('icons', icon_files)]
OPTIONS = {
    'argv_emulation': False,  # Disable to avoid Carbon framework dependency
    'excludes': ['Carbon'],  # Exclude deprecated Carbon framework
    'iconfile': 'app_icon.icns',  # Use the app icon
    
    'plist': {
        'CFBundleName': 'MacMuteOnLocation',
        'CFBundleDisplayName': 'MacMuteOnLocation',
        'CFBundleIdentifier': 'com.macmuteonlocation.app',
        'CFBundleVersion': version,
        'CFBundleShortVersionString': version,
        'CFBundleIconFile': 'app_icon.icns',  # Specify icon in plist
        'LSUIElement': True,  # Hide from dock
        'NSLocationUsageDescription': 'This app needs location access to automatically mute/unmute based on your location.',
        'NSLocationWhenInUseUsageDescription': 'This app needs location access to automatically mute/unmute based on your location.',
        'NSLocationAlwaysAndWhenInUseUsageDescription': 'This app needs location access to automatically mute/unmute based on your location.',
        'NSHighResolutionCapable': True,
    },
    'packages': ['rumps'],
    'includes': ['objc', 'json', 'os', 'math', 'threading', 'traceback', 'jaraco.text', 'jaraco'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name='MacMuteOnLocation',
    version=version,
    description='Automatically mute/unmute Mac based on location',
    author='Your Name',
    author_email='your.email@example.com',
)