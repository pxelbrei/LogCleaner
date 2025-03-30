#!/usr/bin/env python3
import os
import glob
import time
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'p.xelbrei'
    __version__ = '1.1.2'
    __license__ = 'GPL3'
    __description__ = 'Manages logs by configurable age/size with storage display.'

    def __init__(self):
        super(LogCleaner, self).__init__()
        self.log_dir = "/var/log/pwnagotchi/"
        self.storage_status = "OK"

    def on_config_changed(self, config):
        # Load user-configurable values
        self.max_log_age_days = config['main']['plugins']['logcleaner']['max_log_age_days']
        self.max_log_size_mb = config['main']['plugins']['logcleaner']['max_log_size_mb']

    def on_loaded(self):
        self.logger.info(f"[LogCleaner] Loaded (Max age: {self.max_log_age_days} days)")

    def on_ui_setup(self, ui):
        ui.add_element('log_status', LabeledValue(
            color='black',
            label='logs:',  # Consistent lowercase
            value='-',
            position=(ui.width() // 2 + 15, 0),
            label_font=ui.get_font('Bold 7'),
            text_font=ui.get_font('7')
        ))

    def _enforce_policies(self):
        # Age-based cleanup
        cutoff = time.time() - (self.max_log_age_days * 86400)
        deleted = 0
        for log_file in glob.glob(os.path.join(self.log_dir, "*.log")):
            try:
                if os.path.getmtime(log_file) < cutoff:
                    os.remove(log_file)
                    deleted += 1
            except Exception as e:
                self.logger.warning(f"[LogCleaner] Failed to delete {log_file}: {e}")

        # Size-based cleanup (if still needed)
        while self.get_log_size_mb() > self.max_log_size_mb:
            oldest = min(glob.glob(os.path.join(self.log_dir, "*.log")), key=os.path.getmtime)
            try:
                os.remove(oldest)
                deleted += 1
            except Exception as e:
                self.logger.error(f"[LogCleaner] Size cleanup failed: {e}")
                break

        return deleted

    def on_internet_available(self, agent):
        deleted = self._enforce_policies()
        current_size = self.get_log_size_mb()
        
        # Update status
        if current_size > self.max_log_size_mb * 0.9:
            self.storage_status = "WARN"
        elif current_size > self.max_log_size_mb:
            self.storage_status = "FULL!"
        else:
            self.storage_status = "OK"

        if deleted:
            self.logger.info(f"[LogCleaner] Cleaned {deleted} files | Size: {current_size:.1f}MB")

# Instantiate
instance = LogCleaner()
