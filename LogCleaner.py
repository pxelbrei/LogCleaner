#!/usr/bin/env python3
import os
import glob
import time
import logging
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'pxelbrei'
    __version__ = '1.5.3'
    __license__ = 'GPLv3'
    __description__ = 'Fixed display version with reliable UI updates'

    def __init__(self):
        Plugin.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Initialize logging
        self._init_logging()
        
        # Default configuration
        self.log_dir = "/etc/pwnagotchi/log/"
        self.max_log_age_days = 7
        self.max_log_size_mb = 10
        self.pos_x = 180  # Better default position
        self.pos_y = 50   
        self.cleanup_interval = 1800
        self.storage_status = "OK"
        self.last_cleanup = 0
        self.last_ui_update = 0
        
        os.makedirs(self.log_dir, exist_ok=True)
        self.logger.info("Plugin initialized (v%s)", self.__version__)

    def _init_logging(self):
        try:
            os.makedirs("/var/log/pwnagotchi/", exist_ok=True)
            handler = logging.FileHandler("/var/log/pwnagotchi/logcleaner.log")
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
        except Exception as e:
            self.logger.error("Log init failed: %s", str(e))

    def on_loaded(self):
        self.logger.info("Plugin loaded successfully")

    def on_ui_setup(self, ui):
        """Initialize UI with proper font handling"""
        try:
            # Use available font constants
            label_font = ui.BOLD_FONT if hasattr(ui, 'BOLD_FONT') else None
            text_font = ui.SMALL_FONT if hasattr(ui, 'SMALL_FONT') else None
            
            ui.add_element(
                'log_status',
                LabeledValue(
                    color='black',
                    label='LOGS:',
                    value='0.0MB/OK',
                    position=(self.pos_x, self.pos_y),
                    label_font=label_font,
                    text_font=text_font
                )
            )
            self.logger.info("UI element added at (%d,%d)", self.pos_x, self.pos_y)
        except Exception as e:
            self.logger.error("UI setup failed: %s", str(e), exc_info=True)

    def on_ui_update(self, ui):
        """Force frequent UI updates"""
        try:
            now = time.time()
            if now - self.last_ui_update >= 1:  # Update every second
                current_size = self._get_log_size_mb()
                status_text = f"{current_size:.1f}MB/{self.storage_status}"
                ui.set('log_status', status_text)
                self.last_ui_update = now
        except Exception as e:
            self.logger.error("UI update error: %s", str(e))

    def _get_log_files(self):
        try:
            files = glob.glob(os.path.join(self.log_dir, "*.log"))
            return sorted(files, key=os.path.getmtime)
        except Exception as e:
            self.logger.error("File scan failed: %s", str(e))
            return []

    def _get_log_size_mb(self):
        try:
            return sum(os.path.getsize(f) for f in self._get_log_files()) / (1024 ** 2)
        except Exception as e:
            self.logger.error("Size calc failed: %s", str(e))
            return 0

    def _clean_logs(self):
        self.logger.info("Starting cleanup...")
        deleted = 0
        try:
            # Age-based cleanup
            cutoff = time.time() - (self.max_log_age_days * 86400)
            for log_file in self._get_log_files():
                if os.path.getmtime(log_file) < cutoff:
                    try:
                        os.remove(log_file)
                        deleted += 1
                    except Exception as e:
                        self.logger.warning("Delete failed: %s", str(e))

            # Size-based cleanup
            current_size = self._get_log_size_mb()
            while current_size > self.max_log_size_mb:
                oldest = next(iter(self._get_log_files()), None)
                if not oldest:
                    break
                try:
                    file_size = os.path.getsize(oldest) / (1024 ** 2)
                    os.remove(oldest)
                    current_size -= file_size
                    deleted += 1
                except Exception as e:
                    self.logger.error("Size cleanup error: %s", str(e))
                    break

            self.logger.info("Cleanup done. Deleted: %d, Size: %.2fMB", deleted, current_size)
            return deleted
        except Exception as e:
            self.logger.error("Cleanup crashed: %s", str(e), exc_info=True)
            return 0

    def on_second(self, agent):
        try:
            # Update status
            current_size = self._get_log_size_mb()
            new_status = "FULL!" if current_size > self.max_log_size_mb else \
                        "WARN" if current_size > self.max_log_size_mb * 0.9 else \
                        "OK"
            
            if new_status != self.storage_status:
                self.logger.info("Status changed: %s → %s", self.storage_status, new_status)
                self.storage_status = new_status
            
            # Periodic cleanup
            if time.time() - self.last_cleanup >= self.cleanup_interval:
                self._clean_logs()
                self.last_cleanup = time.time()
        except Exception as e:
            self.logger.error("Second update failed: %s", str(e))

    def on_unload(self, ui):
        try:
            ui.remove_element('log_status')
            self.logger.info("Plugin unloaded")
        except Exception as e:
            self.logger.error("Unload failed: %s", str(e))

# Plugin instance
instance = LogCleaner()
