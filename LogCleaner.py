#!/usr/bin/env python3
import os
import glob
import time
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'pxelbrei'
    __version__ = '1.2.0'
    __license__ = 'GPLv3'
    __description__ = 'Automated log management with customizable display positioning'

    def __init__(self):
        super(LogCleaner, self).__init__()
        self.log_dir = "/var/log/pwnagotchi/"
        self.max_log_age_days = 7
        self.max_log_size_mb = 10
        self.pos_x = 0
        self.pos_y = 0
        self.storage_status = "OK"

    def on_config_changed(self, config):
        # Load configurable parameters
        self.max_log_age_days = config['main']['plugins']['logcleaner']['max_log_age_days']
        self.max_log_size_mb = config['main']['plugins']['logcleaner']['max_log_size_mb']
        
        # Custom display position
        self.pos_x = int(config['main']['plugins']['logcleaner'].get('pos_x', 0))
        self.pos_y = int(config['main']['plugins']['logcleaner'].get('pos_y', 0))

        # Clamp values to reasonable defaults if negative
        display_width = 212  # Waveshare v2 default
        display_height = 104
        self.pos_x = max(-display_width, min(self.pos_x, display_width))
        self.pos_y = max(-display_height, min(self.pos_y, display_height))

    def on_ui_setup(self, ui):
        # Calculate final position (negative values = from right/bottom)
        final_x = self.pos_x if self.pos_x >= 0 else ui.width() + self.pos_x
        final_y = self.pos_y if self.pos_y >= 0 else ui.height() + self.pos_y

        ui.add_element('log_status', LabeledValue(
            color='black',
            label='logs:',
            value='-',
            position=(final_x, final_y),
            label_font=ui.get_font('Bold 7'),
            text_font=ui.get_font('7')
        ))

    def _get_log_files(self):
        return sorted(glob.glob(os.path.join(self.log_dir, "*.log")),
                     key=os.path.getmtime)

    def get_log_size_mb(self):
        try:
            return sum(os.path.getsize(f) for f in self._get_log_files()) / (1024 ** 2)
        except Exception as e:
            self.logger.error(f"[LogCleaner] Size check failed: {e}")
            return 0

    def _clean_logs(self):
        # Age-based cleanup
        cutoff = time.time() - (self.max_log_age_days * 86400)
        deleted = 0
        
        for log_file in self._get_log_files():
            try:
                if os.path.getmtime(log_file) < cutoff:
                    os.remove(log_file)
                    deleted += 1
                    self.logger.debug(f"[LogCleaner] Deleted (age): {os.path.basename(log_file)}")
            except Exception as e:
                self.logger.warning(f"[LogCleaner] Failed to delete {log_file}: {e}")

        # Size-based cleanup if needed
        current_size = self.get_log_size_mb()
        while current_size > self.max_log_size_mb:
            oldest = self._get_log_files()[0]  # Oldest file
            try:
                file_size = os.path.getsize(oldest) / (1024 ** 2)
                os.remove(oldest)
                current_size -= file_size
                deleted += 1
                self.logger.debug(f"[LogCleaner] Deleted (size): {os.path.basename(oldest)}")
            except Exception as e:
                self.logger.error(f"[LogCleaner] Size cleanup failed: {e}")
                break

        return deleted

    def on_internet_available(self, agent):
        deleted = self._clean_logs()
        current_size = self.get_log_size_mb()

        # Update status
        if current_size > self.max_log_size_mb * 0.9:
            self.storage_status = "WARN"
        elif current_size > self.max_log_size_mb:
            self.storage_status = "FULL!"
        else:
            self.storage_status = "OK"

        if deleted:
            self.logger.info(f"[LogCleaner] Cleaned {deleted} files | Current: {current_size:.1f}MB")

    def on_ui_update(self, ui):
        ui.set('log_status', f"{self.get_log_size_mb():.1f}MB/{self.storage_status}")

# Instantiate the plugin
instance = LogCleaner()
