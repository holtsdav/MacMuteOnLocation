#!/usr/bin/env python3

import rumps
import os
import sys
import json
import math
import weakref
import time
import traceback
import subprocess
import plistlib
import urllib.request
import zipfile
import tempfile
import shutil
from AppKit import NSApplication, NSWorkspace

__version__ = "0.1.2"
from Foundation import NSNotificationCenter
from CoreLocation import (
    CLLocationManager, CLGeocoder,
    kCLLocationAccuracyHundredMeters,
    kCLLocationAccuracyBestForNavigation, # Added for more precise one-off requests
    kCLAuthorizationStatusNotDetermined,
    kCLAuthorizationStatusAuthorizedAlways,
    kCLAuthorizationStatusAuthorizedWhenInUse,
    kCLAuthorizationStatusDenied,
    kCLAuthorizationStatusRestricted
)
import objc


# Suppress PyObjC warnings
objc.setVerbose(False)

class LocationMenubarApp(rumps.App):
    """Main menubar application class"""
    
    def __init__(self):
        # Detect system appearance and set appropriate icon
        icon_name = self.get_appropriate_icon()
        super(LocationMenubarApp, self).__init__("MacMuteOnLocation", icon=icon_name, template=True)
        
        # Initialize application state
        self.is_active = False
        self.is_muted = False
        self.inside_target_zone = False
        self.current_location = None
        self.target_locations = []
        self.target_location_coords = {}
        self.location_check_interval = 300  # Default to 5 minutes for better battery life
        self.only_scan_on_wakeup = False  # New setting for wakeup-only scanning
        self.launch_at_login = False
        self.has_prompted_autostart = False
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.last_wake_time = time.time()
        self.woke_from_sleep = False # Flag to indicate if the app just woke from sleep
        
        # Initialize location manager and delegate
        self.location_manager = None
        self.location_delegate_obj = None
        
        # Create menu items with better UX
        self.status_item = rumps.MenuItem("Status: Inactive", icon=os.path.join(self.script_dir, "icons", "status_inactive.png"), template=True, callback=self.toggle_status)
        self.location_item = rumps.MenuItem("Location: Unknown", icon=os.path.join(self.script_dir, "icons", "location.png"), template=True)
        self.enable_location_item = rumps.MenuItem("Enable Location Services in System Settings", icon=os.path.join(self.script_dir, "icons", "settings.png"), template=True, callback=self.open_location_settings)
        self.target_locations_menu = rumps.MenuItem("Target Locations", icon=os.path.join(self.script_dir, "icons", "target.png"), template=True)
        self.mute_item = rumps.MenuItem("Mute Mac", icon=os.path.join(self.script_dir, "icons", "mute.png"), template=True, callback=self.manual_mute_toggle)
        self.interval_item = rumps.MenuItem("Check Interval", icon=os.path.join(self.script_dir, "icons", "interval.png"), template=True) # Title will be set in update_interval_menu
        
        autostart_title = "Disable Auto-Start at Login" if self.is_in_login_items() else "Enable Auto-Start at Login"
        self.autostart_item = rumps.MenuItem(autostart_title, icon=os.path.join(self.script_dir, "icons", "autostart.png"), template=True, callback=self.toggle_autostart)
        
        self.update_item = rumps.MenuItem("Check for Updates", icon=os.path.join(self.script_dir, "icons", "update.png"), template=True, callback=self.check_for_updates)
        
        self.CHECK_INTERVALS = {
            "1 Min": 60,
            "2 Min": 120,
            "5 Min": 300,
            "10 Min": 600,
            "15 Min": 900,
            "30 Min": 1800,
            "1 Hour": 3600
        }
        self.update_interval_menu()
        
        # Create the wakeup-only toggle menu item
        self.wakeup_only_item = rumps.MenuItem("Only Scan on Wakeup", icon=os.path.join(self.script_dir, "icons", "wakeup.png"), template=True, callback=self.toggle_wakeup_only)
        
        # Build menu structure with better organization
        self.menu = [
            self.status_item,
            self.location_item,
            self.enable_location_item,
            None,  # Separator
            self.target_locations_menu,
            self.interval_item, # This will now be a submenu
            self.wakeup_only_item, # New toggle for wakeup-only scanning
            None,  # Separator
            self.mute_item,
            rumps.MenuItem("Refresh Location", icon=os.path.join(self.script_dir, "icons", "refresh.png"), template=True, callback=self.refresh_location),
            None,  # Separator
            self.update_item,
            None,  # Separator
            self.autostart_item,
            None,  # Separator
        ]
        
        # Load target locations and setup
        self.load_target_locations()
        self.save_target_locations()  # Save to convert old format to new format if needed
        self.update_target_locations_menu()
        self.update_interval_menu()  # Update interval menu to reflect loaded setting
        # Manual setup instructions available in menu
        self.setup_location_manager()
        
        # Hide location services menu item initially
        self.enable_location_item.hide()
        
        # Start timers
        self.start_mute_sync_timer()
        
        # Setup wake detection
        self.setup_wake_detection()
        
        # Schedule first-time autostart prompt
        rumps.Timer(self.prompt_autostart_if_needed, 2).start()
        
        # Template mode handles icon adaptation automatically
        print("Template mode enabled - icon adapts automatically to system appearance and wallpaper brightness")
        
    def get_appropriate_icon(self):
        """Get the appropriate icon for template mode"""
        # With template mode enabled, use the dark icon which will be automatically
        # inverted by macOS when needed (e.g., with light wallpapers in dark mode)
        return "location_dark.png"
        
    def toggle_status(self, _):
        """Toggle between Active and Inactive status"""
        self.is_active = not self.is_active
        self.update_status()
        
        if self.is_active:
            print("Application activated")
            # Show immediate feedback
            rumps.notification("MacMuteOnLocation", "Status Changed", "Application is now ACTIVE - Location monitoring started", sound=False)
            self.start_location_timer()

        else:
            print("Application deactivated")
            rumps.notification("MacMuteOnLocation", "Status Changed", "Application is now INACTIVE - Location monitoring stopped", sound=False)
            self.stop_location_timer()

        
        # Save the status change
        self.save_target_locations()
            
    def setup_location_manager(self):
        """Setup Core Location manager"""
        try:
            self.location_manager = CLLocationManager.alloc().init()
            self.location_delegate_obj = LocationDelegate.alloc().initWithApp_(self)
            self.location_manager.setDelegate_(self.location_delegate_obj)
            self.location_manager.setDesiredAccuracy_(kCLLocationAccuracyHundredMeters)
            
            # Check authorization status
            auth_status = CLLocationManager.authorizationStatus()
            print(f"Current location authorization status: {auth_status}")
            
            if auth_status == kCLAuthorizationStatusNotDetermined:
                print("Requesting location authorization...")
                self.location_manager.requestWhenInUseAuthorization()
            elif auth_status in [kCLAuthorizationStatusAuthorizedAlways, kCLAuthorizationStatusAuthorizedWhenInUse]:
                print("Location already authorized")
                self.enable_location_item.hide()
                # Don't start continuous updates here - only when needed
            else:
                print(f"Location access denied or restricted: {auth_status}")
                self.enable_location_item.show()
                self.location_item.title = "Location: Access Denied"
                
        except Exception as e:
            print(f"Error setting up location manager: {e}")
            traceback.print_exc()
    
    def open_location_settings(self, _):
        """Open System Preferences to Location Services settings"""
        os.system("open 'x-apple.systempreferences:com.apple.preference.security?Privacy_LocationServices'")
    
    def update_location_authorization_ui(self, status):
        """Update UI based on location authorization status"""
        if status in [kCLAuthorizationStatusAuthorizedAlways, kCLAuthorizationStatusAuthorizedWhenInUse]:
            self.enable_location_item.hide()
        else:
            self.enable_location_item.show()
            if status == kCLAuthorizationStatusDenied:
                self.location_item.title = "Location: Access Denied"
    
    def location_updated(self, location):
        """Called when location is updated"""
        try:
            self.current_location = location
            lat = location.coordinate().latitude
            lon = location.coordinate().longitude
            
            print(f"Location updated: {lat}, {lon}")
            
            # Reverse geocode to get street name
            def reverse_geocode_callback(placemarks, error):
                try:
                    if error is None and placemarks and len(placemarks) > 0:
                        placemark = placemarks[0]
                        street = placemark.thoroughfare()
                        if not street:
                            street = placemark.name()
                        
                        if street:
                            self.location_item.title = f"Location: {street}"
                        else:
                            self.location_item.title = f"Location: {lat:.4f}, {lon:.4f}"
                except Exception as e:
                    print(f"Error in reverse geocode callback: {e}")

            geocoder = CLGeocoder.alloc().init()
            geocoder.reverseGeocodeLocation_completionHandler_(location, reverse_geocode_callback)
            
            # Check if we're in any target zones
            if hasattr(self.location_delegate_obj, 'check_target_locations'):
                self.location_delegate_obj.check_target_locations(lat, lon)
                
        except Exception as e:
            print(f"Error processing location update: {e}")
            traceback.print_exc()
            self.location_item.title = "Location: Error"
    
    def stop_location_updates(self):
        """Stop location updates"""
        if self.location_manager:
            print("Stopping location updates")
            self.location_manager.stopUpdatingLocation()
    
    def stop_location_updates_and_reset_accuracy(self):
        """Stop location updates and reset accuracy to normal"""
        if self.location_manager:
            print("Stopping location updates and resetting accuracy")
            self.location_manager.stopUpdatingLocation()
            self.location_manager.setDesiredAccuracy_(kCLLocationAccuracyHundredMeters)
    
    def toggle_wakeup_only(self, _):
        """Toggle between regular interval scanning and wakeup-only scanning"""
        self.only_scan_on_wakeup = not self.only_scan_on_wakeup
        
        # Update menu item to show current state
        if self.only_scan_on_wakeup:
            self.wakeup_only_item.title = "✓ Only Scan on Wakeup"
            self.update_interval_menu()
            # Stop the timer if it's running
            self.stop_location_timer()
            rumps.notification("MacMuteOnLocation", "Scan Mode Changed", "Only scanning on wakeup - interval scanning disabled", sound=False)
        else:
            self.wakeup_only_item.title = "Only Scan on Wakeup"
            # Update interval menu to show current interval
            self.update_interval_menu()
            # Restart the timer if app is active
            if self.is_active:
                self.start_location_timer()
            rumps.notification("MacMuteOnLocation", "Scan Mode Changed", "Regular interval scanning enabled", sound=False)
        
        # Save the setting
        self.save_target_locations()
    
    def start_location_timer(self):
        """Start the location checking timer"""
        self.stop_location_timer()
        if self.is_active and not self.only_scan_on_wakeup:
            self.location_timer = rumps.Timer(self.location_timer_callback, self.location_check_interval)
            self.location_timer.start()
    
    def stop_location_timer(self):
        """Stop the location checking timer"""
        if hasattr(self, 'location_timer') and self.location_timer:
            self.location_timer.stop()
            self.location_timer = None
    
    def location_timer_callback(self, sender=None):
        """Timer callback for location checks"""
        print(f"Location timer callback. Active: {self.is_active}")
        if self.is_active and self.location_manager:
            try:
                auth_status = CLLocationManager.authorizationStatus()
                if auth_status in [kCLAuthorizationStatusAuthorizedAlways, kCLAuthorizationStatusAuthorizedWhenInUse]:
                    print("Timer: Requesting location update...")
                    # Update UI to show we're checking location
                    self.location_item.title = "Location: Updating..."
                    # Request single location update for better battery efficiency
                    self.location_manager.requestLocation()
                else:
                    print("Timer: Location not authorized for timer callback")
                    self.location_item.title = "Location: Access Denied"
                    self.update_location_authorization_ui(auth_status)
            except Exception as e:
                print(f"Error in location timer callback: {e}")
                traceback.print_exc()
                self.location_item.title = "Location: Error"
    
    def start_mute_sync_timer(self):
        """Start timer to sync mute state with system"""
        self.stop_mute_sync_timer()
        # Increase sync interval to 10 seconds for better performance
        self.mute_sync_timer = rumps.Timer(self.mute_sync_callback, 10.0)
        self.mute_sync_timer.start()
    
    def stop_mute_sync_timer(self):
        """Stop the mute sync timer"""
        if hasattr(self, 'mute_sync_timer') and self.mute_sync_timer:
            self.mute_sync_timer.stop()
            self.mute_sync_timer = None
    
    def mute_sync_callback(self, sender=None):
        """Sync internal mute state with system mute state"""
        try:
            result = subprocess.run(["osascript", "-e", "output muted of (get volume settings)"], capture_output=True, text=True)
            system_muted = result.stdout.strip().lower() == 'true'
            
            if self.is_muted != system_muted:
                self.is_muted = system_muted
                if self.is_muted:
                    self.mute_item.title = "Unmute Mac"
                    self.mute_item.icon = os.path.join(self.script_dir, "icons", "unmute.png")
                else:
                    self.mute_item.title = "Mute Mac"
                    self.mute_item.icon = os.path.join(self.script_dir, "icons", "mute.png")
                
        except Exception as e:
            print(f"Error syncing mute state: {e}")
    
    def manual_mute_toggle(self, _):
        """Manually toggle mute state"""
        try:
            if self.is_muted:
                os.system("osascript -e 'set volume without output muted'")
                print("Manual unmute")
                self.is_muted = False
                self.mute_item.title = "Mute Mac"
                self.mute_item.icon = os.path.join(self.script_dir, "icons", "mute.png")
            else:
                os.system("osascript -e 'set volume with output muted'")
                print("Manual mute")
                self.is_muted = True
                self.mute_item.title = "Unmute Mac"
                self.mute_item.icon = os.path.join(self.script_dir, "icons", "unmute.png")
        except Exception as e:
            print(f"Error in manual mute toggle: {e}")
    
    # calculate_distance removed in favor of CLLocation.distanceFromLocation_
    
    def geocode_target_location(self, address):
        """Geocode a target location address to get coordinates"""
        def geocode_callback(placemarks, error):
            try:
                if error is not None:
                    print(f"Geocoding error for {address}: {error}")
                    return
                    
                if placemarks and len(placemarks) > 0:
                    placemark = placemarks[0]
                    location = placemark.location()
                    if location:
                        lat = location.coordinate().latitude
                        lon = location.coordinate().longitude
                        self.target_location_coords[address] = (lat, lon)
                        print(f"Geocoded {address}: {lat}, {lon}")
                        
                        # Re-check distances now that we have coordinates
                        if self.current_location:
                            current_lat = self.current_location.coordinate().latitude
                            current_lon = self.current_location.coordinate().longitude
                            if hasattr(self.location_delegate_obj, 'check_target_locations'):
                                self.location_delegate_obj.check_target_locations(current_lat, current_lon)
            except Exception as e:
                print(f"Error in geocode callback for {address}: {e}")
                traceback.print_exc()
        
        geocoder = CLGeocoder.alloc().init()
        geocoder.geocodeAddressString_completionHandler_(address, geocode_callback)
    
    def auto_mute(self, should_mute):
        """Automatically mute or unmute the Mac based on location"""
        try:
            if should_mute:
                print("auto_mute: Attempting to mute Mac.")
                os.system("osascript -e 'set volume with output muted'")
                rumps.notification("MacMuteOnLocation", "Auto Muted", "Mac muted - entered target zone", sound=False)
            else:
                print("auto_mute: Attempting to unmute Mac.")
                os.system("osascript -e 'set volume without output muted'")
                rumps.notification("MacMuteOnLocation", "Auto Unmuted", "Mac unmuted - left target zone", sound=False)
            
            # Update internal state and menu button text
            if self.is_muted != should_mute:
                self.is_muted = should_mute
                # Update the mute button text to reflect the new state
                if self.is_muted:
                    self.mute_item.title = "Unmute Mac"
                    self.mute_item.icon = os.path.join(self.script_dir, "icons", "unmute.png")
                else:
                    self.mute_item.title = "Mute Mac"
                    self.mute_item.icon = os.path.join(self.script_dir, "icons", "mute.png")
                
        except Exception as e:
            print(f"Error in auto_mute: {e}")
            traceback.print_exc()
    
    def _delayed_stop_location_updates(self, sender):
        self.stop_location_updates_and_reset_accuracy()
        sender.stop()

    def refresh_location(self, _):
        """Manually refresh location"""
        print("Manual location refresh requested")
        
        self.location_item.title = "Location: Refreshing..."
        try:
            auth_status = CLLocationManager.authorizationStatus()
            if self.location_manager and auth_status in [kCLAuthorizationStatusAuthorizedAlways, kCLAuthorizationStatusAuthorizedWhenInUse]:
                print("Requesting immediate location for manual refresh...")
                # Set higher accuracy for manual refresh
                self.location_manager.setDesiredAccuracy_(kCLLocationAccuracyBestForNavigation)
                # Use startUpdatingLocation for better reliability
                self.location_manager.startUpdatingLocation()
                # Stop after getting location update
                timer = rumps.Timer(self._delayed_stop_location_updates, 10.0)
                timer.start()
            else:
                self.enable_location_item.show()
                self.update_location_authorization_ui(auth_status)
                self.location_item.title = "Location: Access Denied"
                rumps.alert("Location Access Required", f"Please enable location services to refresh location. Authorization status: {auth_status}")
        except Exception as e:
            print(f"Error refreshing location: {e}")
            traceback.print_exc()
            self.location_item.title = "Location: Error"
    
    def update_status(self, active=None):
        """Update the status menu item to show Active or Inactive"""
        if active is not None:
            self.is_active = active
            
        # Update menu item text based on status with visual indicators
        if self.is_active:
            self.status_item.title = "Status: Active"
            self.status_item.icon = os.path.join(self.script_dir, "icons", "status_active.png")
        else:
            self.status_item.title = "Status: Inactive"
            self.status_item.icon = os.path.join(self.script_dir, "icons", "status_inactive.png")

    def load_target_locations(self):
        """Load target locations and settings from JSON file"""
        try:
            locations_file = os.path.join(self.script_dir, 'target_locations.json')
            if os.path.exists(locations_file):
                with open(locations_file, 'r') as f:
                    data = json.load(f)
                    
                # Handle both old format (list) and new format (dict)
                if isinstance(data, list):
                    # Old format - just locations
                    self.target_locations = data
                elif isinstance(data, dict):
                    # New format - locations and settings
                    self.target_locations = data.get('locations', [])
                    saved_interval = data.get('settings', {}).get('check_interval', 30)
                    self.location_check_interval = saved_interval
                    print(f"Loaded check interval: {saved_interval}s")
                    
                    # Load status setting
                    saved_status = data.get('settings', {}).get('is_active', False)
                    self.is_active = saved_status
                    self.update_status()
                    print(f"Loaded status: {'Active' if saved_status else 'Inactive'}")
                    
                    # Load wakeup-only setting
                    saved_wakeup_only = data.get('settings', {}).get('only_scan_on_wakeup', False)
                    self.only_scan_on_wakeup = saved_wakeup_only
                    print(f"Loaded only_scan_on_wakeup: {saved_wakeup_only}")
                    
                    self.has_prompted_autostart = data.get('settings', {}).get('has_prompted_autostart', False)
                    
                    # Update wakeup-only menu item
                    if self.only_scan_on_wakeup:
                        self.wakeup_only_item.title = "✓ Only Scan on Wakeup"
                        self.interval_item.title = "Check Interval: Disabled"
                    else:
                        self.wakeup_only_item.title = "Only Scan on Wakeup"
                    
                    # Start location timer if app was active and not in wakeup-only mode
                    if self.is_active and not self.only_scan_on_wakeup:
                        self.start_location_timer()
                    
                # Geocode all target locations on startup
                for location in self.target_locations:
                    address = location['address']
                    if address not in self.target_location_coords:
                        self.geocode_target_location(address)
        except Exception as e:
            print(f"Error loading target locations: {e}")
            self.target_locations = []
    
    def save_target_locations(self):
        """Save target locations and settings to JSON file"""
        try:
            locations_file = os.path.join(self.script_dir, 'target_locations.json')
            data = {
                'locations': self.target_locations,
                'settings': {
                    'check_interval': self.location_check_interval,
                    'is_active': self.is_active,
                    'only_scan_on_wakeup': self.only_scan_on_wakeup,
                    'has_prompted_autostart': self.has_prompted_autostart
                }
            }
            with open(locations_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved locations and settings (interval: {self.location_check_interval}s, only_scan_on_wakeup: {self.only_scan_on_wakeup})")
        except Exception as e:
            print(f"Error saving target locations: {e}")
    
    def update_target_locations_menu(self):
        """Update the Target Locations submenu"""
        # Clear existing menu items
        try:
            self.target_locations_menu.clear()
        except AttributeError:
            pass  # Handle case where submenu not initialized
        
        # Add existing locations
        for i, location in enumerate(self.target_locations):
            menu_item = rumps.MenuItem(
                f"{location['address']} ({location['radius']}m)",
                callback=lambda x, idx=i: self.edit_location(idx)
            )
            self.target_locations_menu.add(menu_item)
        
        # Add separator if there are locations
        if self.target_locations:
            self.target_locations_menu.add(None)
        
        # Add the Add Location button
        self.target_locations_menu.add(rumps.MenuItem(
            "+ Add Location",
            callback=lambda x: self.add_location()
        ))
    
    def add_location(self):
        """Show window to add a new location"""
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        # Get address first
        address_response = rumps.Window(
            message='Enter the address for the target location',
            title='Add Target Location - Address',
            default_text='',
            dimensions=(320, 22)
        ).run()
        
        if not address_response.clicked or not address_response.text.strip():
            return
        
        address = address_response.text.strip()
        
        # Get radius second
        radius_response = rumps.Window(
            message='Enter the radius in meters for the target location',
            title='Add Target Location - Radius',
            default_text='100',
            dimensions=(200, 22)
        ).run()
        
        if radius_response.clicked:
            try:
                radius = int(radius_response.text.strip())
                
                if radius <= 0:
                    rumps.alert("Invalid Input", "Radius must be a positive number")
                    return
                
                # Add new location
                self.target_locations.append({
                    'address': address,
                    'radius': radius
                })
                
                # Geocode the new location
                self.geocode_target_location(address)
                
                # Save and update menu
                self.save_target_locations()
                self.update_target_locations_menu()
            except ValueError:
                rumps.alert("Invalid Input", "Radius must be a number")
    
    def edit_location(self, index):
        """Show window to edit or delete an existing location"""
        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        location = self.target_locations[index]
        
        # Show options: Edit or Delete using rumps.alert for a cleaner UI
        action_response = rumps.alert(
            title='Edit Target Location',
            message=f'Current location: {location["address"]} ({location["radius"]}m)\n\nChoose an action:',
            ok='Edit',
            cancel='Delete'
        )
        # rumps.alert returns 1 for OK, 0 for Cancel
        
        if action_response == 1:  # User clicked "Edit"
            # Edit the location
            # Get new address
            address_response = rumps.Window(
                message='Enter the new address for the target location',
                title='Edit Target Location - Address',
                default_text=location['address'],
                dimensions=(320, 22)
            ).run()
            
            if not address_response.clicked or not address_response.text.strip():
                # User cancelled or entered empty address during edit
                return
            
            address = address_response.text.strip()
            
            # Get new radius
            radius_response = rumps.Window(
                message='Enter the new radius in meters for the target location',
                title='Edit Target Location - Radius',
                default_text=str(location['radius']),
                dimensions=(200, 22)
            ).run()
            
            if radius_response.clicked:
                try:
                    radius = int(radius_response.text.strip())
                    
                    if radius <= 0:
                        rumps.alert("Invalid Input", "Radius must be a positive number")
                        return
                    
                    # Update location
                    old_address = self.target_locations[index]['address']
                    self.target_locations[index] = {
                        'address': address,
                        'radius': radius
                    }
                    
                    # Remove old coordinates if address changed
                    if old_address != address:
                        if old_address in self.target_location_coords:
                            del self.target_location_coords[old_address]
                        # Geocode the new address
                        self.geocode_target_location(address)
                except ValueError:
                    rumps.alert("Invalid Input", "Radius must be a number")
                    return
            else:
                # User cancelled radius input
                return

        elif action_response == 0:  # User clicked "Delete"
            # Delete location
            address_to_delete = self.target_locations[index]['address']
            print(f"Deleting location: {address_to_delete}")
            if address_to_delete in self.target_location_coords:
                del self.target_location_coords[address_to_delete]
            del self.target_locations[index]
        else:
            # User might have closed the alert window in some other way (e.g. Esc key)
            # or an unexpected response code was received.
            print(f"Edit/Delete action cancelled or unexpected response: {action_response}")
            return # Do nothing further
        
        # Save and update menu
        self.save_target_locations()
        self.update_target_locations_menu()

    def update_interval_menu(self):
        """Update the interval submenu with available options and current selection."""
        # Only clear if the submenu has been initialized (i.e., _menu is not None)
        if self.interval_item._menu is not None:
            self.interval_item.clear()
        else:
            # If _menu is None, it's the first population (e.g., during __init__).
            # Ensure the Python-side dictionary is also clear for consistency,
            # as rumps.MenuItem.clear() would normally handle this.
            # Adding items below will create/initialize self.interval_item._menu.
            self.interval_item._dict = {}
        
        # If only_scan_on_wakeup is enabled, show interval as disabled
        if self.only_scan_on_wakeup:
            self.interval_item.title = "Check Interval: Disabled"
            # Still add the menu items but indicate they're disabled
            for label, secs in self.CHECK_INTERVALS.items():
                menu_label = f"{label} (Disabled)"
                # Add items but with a disabled callback
                self.interval_item.add(rumps.MenuItem(menu_label, callback=lambda _: rumps.notification("MacMuteOnLocation", "Interval Disabled", "Disable 'Only Scan on Wakeup' to change interval", sound=False)))
            return
        
        # Normal interval menu when only_scan_on_wakeup is disabled
        current_interval_label = "Unknown"
        for label, secs in self.CHECK_INTERVALS.items():
            if secs == self.location_check_interval:
                current_interval_label = label
                # Add a checkmark or similar indicator for the current interval
                menu_label = f"✓ {label}"
            else:
                menu_label = label
            self.interval_item.add(rumps.MenuItem(menu_label, callback=lambda _, l=label, s=secs: self.set_interval_action(l, s)))
        self.interval_item.title = f"Check Interval: {current_interval_label}"

    def set_interval_action(self, label, seconds):
        """Action called when an interval is selected from the menu."""
        if seconds >= 60:
            old_interval = self.location_check_interval
            self.location_check_interval = seconds
            print(f"Location check interval changed from {old_interval}s to {seconds}s ({label})")
            rumps.notification("MacMuteOnLocation", "Interval Updated", f"Location check interval set to {label}", sound=False)
            self.update_interval_menu() # Update menu to reflect new selection
            self.save_target_locations() # Save the new interval setting
            if self.is_active:
                self.start_location_timer()
        else:
            rumps.alert("Invalid Input", "Interval must be at least 1 minute for optimal battery life.")

    # Keep a reference to the old set_interval if needed, or remove if fully replaced
    # For now, we are replacing the direct input with a menu selection system
    # def set_interval(self, _): # This is the old method, now replaced by menu actions
    #     ...

    def prompt_autostart_if_needed(self, sender=None):
        if sender:
            sender.stop()
            
        if not self.has_prompted_autostart:
            self.has_prompted_autostart = True
            self.save_target_locations()
            
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            response = rumps.alert(
                title='MacMuteOnLocation',
                message='Would you like to start MacMuteOnLocation automatically when you log in?\n\nYou can always change this later from the menu bar.',
                ok='Yes',
                cancel='No'
            )
            
            if response == 1:
                if not self.is_in_login_items():
                    self.toggle_autostart(self.autostart_item)

    def check_for_updates(self, _):
        """Check GitHub for updates, and if found, download and replace"""
        self.update_item.title = "Checking..."
        
        try:
            req = urllib.request.Request("https://api.github.com/repos/holtsdav/MacMuteOnLocation/releases/latest")
            req.add_header('User-Agent', 'MacMuteOnLocation-Updater')
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            latest_version = data.get('tag_name', '').lstrip('v')
            
            if not latest_version:
                raise Exception("Could not determine latest version")
                
            latest_parts = [int(x) for x in latest_version.split('.')]
            current_parts = [int(x) for x in __version__.split('.')]
            
            if latest_parts <= current_parts:
                rumps.alert("Up to date", f"You are running the latest version ({__version__}).")
                self.update_item.title = "Check for Updates"
                return
                
            if '.app/Contents/MacOS' not in sys.executable:
                rumps.alert(
                    "Update Available", 
                    f"Version {latest_version} is available, but you are running from source. Please update manually via git pull."
                )
                self.update_item.title = "Check for Updates"
                return
                
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            response = rumps.alert(
                title='Update Available',
                message=f'Version {latest_version} is available (Current: {__version__}).\nWould you like to install it now? The app will restart.',
                ok='Update Now',
                cancel='Later'
            )
            
            if response == 1:
                self._perform_update(data)
            else:
                self.update_item.title = "Check for Updates"
                
        except Exception as e:
            rumps.alert("Update Failed", f"Failed to check for updates: {e}")
            self.update_item.title = "Check for Updates"
            traceback.print_exc()
            
    def _perform_update(self, release_data):
        self.update_item.title = "Downloading..."
        
        assets = release_data.get('assets', [])
        zip_url = None
        for asset in assets:
            if asset.get('name', '').endswith('.zip'):
                zip_url = asset.get('browser_download_url')
                break
                
        if not zip_url:
            rumps.alert("Error", "No pre-built app zip found in the release.")
            self.update_item.title = "Check for Updates"
            return
            
        try:
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "update.zip")
            urllib.request.urlretrieve(zip_url, zip_path)
            
            self.update_item.title = "Extracting..."
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            extracted_app = os.path.join(temp_dir, "MacMuteOnLocation.app")
            if not os.path.exists(extracted_app):
                for root, dirs, files in os.walk(temp_dir):
                    if "MacMuteOnLocation.app" in dirs:
                        extracted_app = os.path.join(root, "MacMuteOnLocation.app")
                        break
                        
            if not os.path.exists(extracted_app):
                raise Exception("Could not find MacMuteOnLocation.app in the downloaded archive.")
                
            current_app_path = sys.executable.split('.app/Contents/MacOS')[0] + '.app'
            script_path = os.path.join(temp_dir, "update.sh")
            
            script_content = f'''#!/bin/bash
sleep 2
rm -rf "{current_app_path}"
mv "{extracted_app}" "{current_app_path}"
open "{current_app_path}"
rm -rf "{temp_dir}"
'''
            with open(script_path, 'w') as f:
                f.write(script_content)
                
            os.chmod(script_path, 0o755)
            subprocess.Popen([script_path], start_new_session=True)
            rumps.quit_application()
            
        except Exception as e:
            rumps.alert("Error", f"Failed to install update: {e}")
            self.update_item.title = "Check for Updates"
            traceback.print_exc()

    def is_in_login_items(self):
        """Check if the app is in the user's login items"""
        try:
            result = subprocess.run(
                ["osascript", "-e", 'tell application "System Events" to get name of every login item'],
                capture_output=True, text=True
            )
            return "MacMuteOnLocation" in result.stdout
        except Exception:
            return False

    def toggle_autostart(self, sender):
        """Toggle auto-start at login by adding/removing from System Events Login Items"""
        if '.app/Contents/MacOS' not in sys.executable:
            rumps.alert("Not Supported", "Auto-start via Login Items only works when running the compiled App bundle. Please run build_app.sh and use the generated MacMuteOnLocation.app.")
            return
            
        app_path = sys.executable.split('.app/Contents/MacOS')[0] + '.app'
        
        if self.is_in_login_items():
            # Remove it
            script = 'tell application "System Events" to delete (every login item whose name is "MacMuteOnLocation")'
            try:
                subprocess.run(["osascript", "-e", script], check=True)
                sender.title = "Enable Auto-Start at Login"
                rumps.notification("Auto-Start Disabled", "", "Removed from Login Items.")
            except Exception as e:
                rumps.alert("Error", f"Failed to disable auto-start: {e}")
        else:
            # Add it
            script = f'tell application "System Events" to make login item at end with properties {{path:"{app_path}", hidden:false}}'
            try:
                subprocess.run(["osascript", "-e", script], check=True)
                sender.title = "Disable Auto-Start at Login"
                rumps.notification("Auto-Start Enabled", "", "Added to Login Items.")
            except Exception as e:
                rumps.alert("Error", f"Failed to enable auto-start: {e}")

    def setup_wake_detection(self):
        """Setup system wake detection using NSWorkspace notifications"""
        try:
            workspace = NSWorkspace.sharedWorkspace()
            notification_center = workspace.notificationCenter()
            
            # Register for wake notifications
            notification_center.addObserver_selector_name_object_(
                self,
                "systemDidWake:",
                "NSWorkspaceDidWakeNotification",
                None
            )
            
            # Register for sleep notifications
            notification_center.addObserver_selector_name_object_(
                self,
                "systemWillSleep:",
                "NSWorkspaceWillSleepNotification",
                None
            )
            
            print("Wake detection setup complete")
        except Exception as e:
            print(f"Error setting up wake detection: {e}")
    
    def systemDidWake_(self, notification):
        """Called when system wakes up"""
        print("System wake detected")
        self.last_wake_time = time.time()
        self.woke_from_sleep = True # Set flag when system wakes
        
        if self.is_active:
            # Immediately check location after wake
            print("Requesting immediate location update after wake")
            self.location_item.title = "Location: Checking after wake..."
            
            # Request immediate location update
            if self.location_manager:
                try:
                    auth_status = CLLocationManager.authorizationStatus()
                    if auth_status in [kCLAuthorizationStatusAuthorizedAlways, kCLAuthorizationStatusAuthorizedWhenInUse]:
                        self.location_manager.requestLocation()
                except Exception as e:
                    print(f"Error requesting location after wake: {e}")
    
    def systemWillSleep_(self, notification):
        """Called when system is about to sleep"""
        print("System will sleep")
    
    def quit_app(self, _):
        print("Quitting application gracefully...")
        self.is_active = False
        self.stop_location_timer()
        self.stop_mute_sync_timer()

        
        if hasattr(self, 'location_manager') and self.location_manager:
            print("Stopping CoreLocation manager updates.")
            self.location_manager.stopUpdatingLocation()
            self.location_manager.setDelegate_(None)
            print("CoreLocation manager delegate unset.")

        print("Calling rumps.quit_application().")
        rumps.quit_application()


class LocationDelegate(objc.lookUpClass('NSObject')):
    """Location delegate that handles Core Location callbacks"""
    
    def initWithApp_(self, app):
        """Initialize with the main app instance"""
        self = objc.super(LocationDelegate, self).init()
        if self is not None:
            self.app = weakref.ref(app)
        return self

    def locationManager_didUpdateLocations_(self, manager, locations):
        """Called when new location data is available"""
        print("Location update received!")
        if locations and len(locations) > 0:
            location = locations[-1]
            try:
                # Call the app's location_updated method
                app = self.app()
                if app:
                    app.location_updated(location)
            except Exception as e:
                print(f"Error in location callback: {e}")
                traceback.print_exc()
    
    def locationManager_didFailWithError_(self, manager, error):
        """Called when there's an error getting location"""
        print(f"Location error: {error}")
        error_code = error.code() if hasattr(error, 'code') else 'Unknown'
        error_description = str(error.localizedDescription()) if hasattr(error, 'localizedDescription') else str(error)
        print(f"Location error details - Code: {error_code}, Description: {error_description}")
        
        # Update UI to show error
        app = self.app()
        if app and hasattr(app, 'location_item'):
            app.location_item.title = "Location: Error"
        
        # Stop location updates on error
        manager.stopUpdatingLocation()
    
    def locationManager_didChangeAuthorizationStatus_(self, manager, status):
        """Called when the authorization status changes"""
        status_string = "Unknown"
        if status == kCLAuthorizationStatusNotDetermined:
            status_string = "Not Determined"
        elif status == kCLAuthorizationStatusAuthorizedAlways or status == kCLAuthorizationStatusAuthorizedWhenInUse:
            status_string = "Authorized"
            print(f"Authorization status: {status_string}. Location access granted.")
            # Don't automatically start continuous updates - only when needed
        elif status == kCLAuthorizationStatusDenied:
            status_string = "Denied"
        elif status == kCLAuthorizationStatusRestricted:
            status_string = "Restricted"
        
        print(f"Location authorization status changed to: {status_string}")
        # Update UI based on new status
        app = self.app()
        if app and hasattr(app, 'update_location_authorization_ui'):
            app.update_location_authorization_ui(status)

    def check_target_locations(self, current_lat, current_lon):
        """Check if current location is within radius of any target location"""
        app = self.app()
        if not app:
            return
            
        print(f"Checking target locations - Active: {app.is_active}, Target count: {len(app.target_locations)}")
        if not app.is_active:
            print("App is inactive, skipping location check for mute logic")
            return
        if not app.target_locations:
            print("No target locations configured, skipping mute logic")
            return
            
        currently_inside_any_target = False
        
        # Create CLLocation for current position
        from CoreLocation import CLLocation
        current_loc = CLLocation.alloc().initWithLatitude_longitude_(current_lat, current_lon)
        
        for target in app.target_locations:
            address = target['address']
            radius = target['radius']
            
            if address in app.target_location_coords:
                target_lat, target_lon = app.target_location_coords[address]
                target_loc = CLLocation.alloc().initWithLatitude_longitude_(target_lat, target_lon)
                distance = current_loc.distanceFromLocation_(target_loc)
                
                print(f"Distance to {address}: {distance:.0f}m (radius: {radius}m)")
                
                if distance <= radius:
                    currently_inside_any_target = True
                    print(f"Currently inside target zone: {address}")
                    break 
            else:
                print(f"Coordinates for {address} not yet geocoded. Requesting geocode.")
                app.geocode_target_location(address)
        
        app.inside_target_zone = currently_inside_any_target

        if app.woke_from_sleep:
            print("Processing location check after wake-up.")
            if app.inside_target_zone:
                if not app.is_muted:
                    print("Inside target zone after wake and Mac is not muted - Muting Mac.")
                    app.auto_mute(True)
            # else: if outside target zone after wake, do nothing as per new requirement
            #    print("Outside target zone after wake - no mute/unmute action taken.")
            app.woke_from_sleep = False # Reset the flag
        else:
            # Regular interval check logic (original behavior)
            if app.inside_target_zone:
                if not app.is_muted:
                    print("Inside target zone (interval check) and Mac is not muted - Muting Mac.")
                    app.auto_mute(True)
            else:
                if app.is_muted:
                    # Only unmute if it wasn't manually muted. 
                    # For now, we assume auto_mute(False) handles this, or we might need more state
                    # if manual mutes should persist even outside zones during interval checks.
                    # The current request is specific to wake-up, so keeping interval unmuting as is.
                    print("Outside target zone (interval check) and Mac is muted - Unmuting Mac.")
                    app.auto_mute(False)


def check_single_instance():
    """Check if another instance of the app is already running"""
    import subprocess
    import os
    import sys
    
    try:
        # Get current process info
        current_pid = os.getpid()
        script_name = os.path.basename(__file__)
        
        # Check for other python processes running this script
        result = subprocess.run(['pgrep', '-f', script_name], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') if pid.strip()]
            # Filter out current process
            other_pids = [pid for pid in pids if pid != current_pid]
            
            if other_pids:
                print(f"Another instance is already running (PID: {other_pids[0]}). Exiting.")
                return False
        
        return True
        
    except Exception as e:
        print(f"Error checking for existing instance: {e}")
        # If we can't check, assume it's safe to continue
        return True


if __name__ == '__main__':
    # Check for existing instance to prevent menubar icon duplication
    if not check_single_instance():
        sys.exit(0)
    
    print("Starting LocationMenubarApp...")
    app = LocationMenubarApp()
    app.run()