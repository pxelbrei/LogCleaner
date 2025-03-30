#!/usr/bin/env python3
import os
import glob
import time
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'pxelbrei'
    __version__ = '1.4.0'
    __license__ = 'GPLv3'
    __description__ = 'Automated log management with configurable retention policies'

    def __init__(self):
        super(LogCleaner, self).__init__()
        # Default path for Jay editions
        self.log_dir = "/etc/pwnagotchi/log/"  
        self.max_log_age_days = 7
        self.max_log_size_mb = 10
        self.pos_x = 0
        self.pos_y = 0
        self.storage_status = "OK"
        self.last_cleanup = 0
        self.cleanup_interval = 3600  # 1 hour in seconds

        # Create log directory if missing
        os.makedirs(self.log_dir, exist_ok=True)

    def on_config_changed(self, config):
        """Load settings from config.toml"""
        try:
            self.log_dir = config['main']['plugins']['logcleaner'].get('log_dir', "/etc/pwnagotchi/log/")
            self.max_log_age_days = int(config['main']['plugins']['logcleaner'].get('max_log_age_days', 7))
            self.max_log_size_mb = int(config['main']['plugins']['logcleaner'].get('max_log_size_mb', 10))
            self.pos_x = int(config['main']['plugins']['logcleaner'].get('pos_x', 0))
            self.pos_y = int(config['main']['plugins']['logcleaner'].get('pos_y', 0))
            self.cleanup_interval = int(config['main']['plugins']['logcleaner'].get('interval', 3600))
            
            # Ensure path ends with /
            self.log_dir = os.path.join(self.log_dir, '')
            
        except Exception as e:
            self.logger.error(f"[LogCleaner] Config error: {e}")

    def on_ui_setup(self, ui):
        """Initialize UI element with configurable position"""
        try:
            # Calculate position (negative values = from edge)
            display_width = ui.width()
            display_height = ui.height()
            pos_x = self.pos_x if self.pos_x >= 0 else display_width + self.pos_x
            pos_y = self.pos_y if self.pos_y >= 0 else display_height + self.pos_y

            ui.add_element('log_status', LabeledValue(
                color='black',
                label='logs:',
                value='-',
                position=(pos_x, pos_y),
                label_font=ui.get_font('Bold 7'),
                text_font=ui.get_font('7')
            ))
        except Exception as e:
            self.logger.error(f"[LogCleaner] UI setup failed: {e}")

    def _get_log_files(self):
        """Get log files sorted by modification time (oldest first)"""
        try:
            return sorted(
                glob.glob(os.path.join(self.log_dir, "*.log")),
                key=os.path.getmtime
            )
        except Exception as e:
            self.logger.error(f"[LogCleaner] File scan failed: {e}")
            return []

    def _get_log_size_mb(self):
        """Calculate total log size in MB"""
        try:
            return sum(os.path.getsize(f) for f in self._get_log_files()) / (1024 ** 2)
        except Exception as e:
            self.logger.error(f"[LogCleaner] Size check failed: {e}")
            return 0

    def _clean_logs(self):
        """Execute cleanup (age + size policies)"""
        if not os.path.exists(self.log_dir):
            self.logger.error(f"[LogCleaner] Log directory missing!")
            return 0

        now = time.time()
        cutoff = now - (self.max_log_age_days * 86400)
        deleted = 0

        # 1. Age-based cleanup
        for log_file in self._get_log_files():
            try:
                if os.path.getmtime(log_file) < cutoff:
                    os.remove(log_file)
                    deleted += 1
                    self.logger.debug(f"[LogCleaner] Deleted (age): {os.path.basename(log_file)}")
            except Exception as e:
                self.logger.warning(f"[LogCleaner] Delete failed: {log_file} ({e})")

        # 2. Size-based cleanup (if needed)
        current_size = self._get_log_size_mb()
        while current_size > self.max_log_size_mb:
            oldest_files = self._get_log_files()
            if not oldest_files:
                break
            oldest = oldest_files[0]  # Oldest file
            try:
                file_size_mb = os.path.getsize(oldest) / (1024 ** 2)
                os.remove(oldest)
                current_size -= file_size_mb
                deleted += 1
                self.logger.debug(f"[LogCleaner] Deleted (size): {os.path.basename(oldest)}")
            except Exception as e:
                self.logger.error(f"[LogCleaner] Size cleanup failed: {e}")
                break

        return deleted

    def on_second(self, agent):
        """Update status every second"""
        try:
            current_time = time.time()
            
            # Update storage status
            current_size = self._get_log_size_mb()
            if current_size > self.max_log_size_mb * 0.9:
                self.storage_status = "WARN"
            elif current_size > self.max_log_size_mb:
                self.storage_status = "FULL!"
            else:
                self.storage_status = "OK"

            # Scheduled cleanup
            if current_time - self.last_cleanup >= self.cleanup_interval:
                deleted = self._clean_logs()
                if deleted:
                    self.logger.info(f"[LogCleaner] Cleaned {deleted} files | Size: {current_size:.1f}MB")
                self.last_cleanup = current_time
                
        except Exception as e:
            self.logger.error(f"[LogCleaner] Runtime error: {e}")

    def on_ui_update(self, ui):
        """Update UI display"""
        try:
            ui.set('log_status', f"{self._get_log_size_mb():.1f}MB/{self.storage_status}")
        except Exception as e:
            self.logger.error(f"[LogCleaner] UI update failed: {e}")

# Plugin instance
instance = LogCleaner()
