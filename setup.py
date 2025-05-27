from setuptools import setup

APP = ['main.py']
DATA_FILES = [('', ['location_dark.png'])]
OPTIONS = {
    'argv_emulation': False,  # Disable to avoid Carbon framework dependency
    'excludes': ['Carbon'],  # Exclude deprecated Carbon framework
    'iconfile': 'app_icon.icns',  # Use the app icon
    
    'plist': {
        'CFBundleName': 'MacMuteOnLocation',
        'CFBundleDisplayName': 'MacMuteOnLocation',
        'CFBundleIdentifier': 'com.macmuteonlocation.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
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
    version='1.0.0',
    description='Automatically mute/unmute Mac based on location',
    author='Your Name',
    author_email='your.email@example.com',
)