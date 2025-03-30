#!/usr/bin/env python3
import os
import glob
import time
import logging
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'pxelbrei'
    __version__ = '1.6.0'
    __license__ = 'GPLv3'
    __description__ = 'Stable log cleaner with reliable display'

    def __init__(self):
        super().__init__()
        self._ready = False
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        self.logger.addHandler(console_handler)
        self.logger.info("Plugin constructing (v%s)", self.__version__)

    def on_loaded(self):
        """Safe delayed initialization"""
        try:
            # Default config
            self.log_dir = "/etc/pwnagotchi/log/"
            self.max_log_age_days = 7
            self.max_log_size_mb = 10
            self.pos_x = 150  # Better visible position
            self.pos_y = 30
            self.text_color = 'black'
            self.cleanup_interval = 3600
            self.storage_status = "OK"
            self.last_cleanup = 0
            
            # Setup file logging
            os.makedirs('/var/log/pwnagotchi/', exist_ok=True)
            file_handler = logging.FileHandler('/var/log/pwnagotchi/logcleaner.log')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            
            os.makedirs(self.log_dir, exist_ok=True)
            self._ready = True
            self.logger.info("Plugin ready")
        except Exception as e:
            self.logger.error("Init failed: %s", str(e))

    def on_ui_setup(self, ui):
        """Initialize display once UI is ready"""
        if not self._ready:
            return
            
        try:
            # Ultra-reliable font setup
            fonts = {
                'label': ('Bold', 8, False),
                'text': ('Small', 8, False)
            }
            
            # Add display element
            ui.add_element(
                'log_status',
                LabeledValue(
                    color=self.text_color,
                    label='LOGS:',
                    value='0.0MB/OK',
                    position=(self.pos_x, self.pos_y),
                    label_font=fonts['label'],
                    text_font=fonts['text']
                )
            )
            self.logger.info("Display setup at (%d,%d)", self.pos_x, self.pos_y)
        except Exception as e:
            self.logger.error("Display setup failed: %s", str(e))

    def on_ui_update(self, ui):
        """Update display content"""
        if not self._ready:
            return
            
        try:
            current_size = self._get_log_size_mb()
            status_text = f"{current_size:.1f}MB/{self.storage_status}"
            ui.set('log_status', status_text)
        except Exception as e:
            self.logger.error("Display update failed: %s", str(e))

    def _get_log_files(self):
        """Safe file listing"""
        try:
            return sorted(glob.glob(os.path.join(self.log_dir, "*.log")), key=os.path.getmtime)
        except:
            return []

    def _get_log_size_mb(self):
        """Calculate log size with fallback"""
        try:
            return sum(os.path.getsize(f) for f in self._get_log_files()) / (1024 ** 2)
        except:
            return 0

    def on_second(self, agent):
        """Main operational loop"""
        if not self._ready:
            return
            
        try:
            # Update status
            current_size = self._get_log_size_mb()
            self.storage_status = (
                "FULL!" if current_size > self.max_log_size_mb else
                "WARN" if current_size > self.max_log_size_mb * 0.9 else
                "OK"
            )
            
            # Periodic cleanup
            if time.time() - self.last_cleanup >= self.cleanup_interval:
                self._clean_logs()
                self.last_cleanup = time.time()
        except Exception as e:
            self.logger.error("Operation error: %s", str(e))

    def _clean_logs(self):
        """Safe log cleanup"""
        try:
            deleted = 0
            cutoff = time.time() - (self.max_log_age_days * 86400)
            
            for log_file in self._get_log_files():
                try:
                    if os.path.getmtime(log_file) < cutoff or \
                       self._get_log_size_mb() > self.max_log_size_mb:
                        os.remove(log_file)
                        deleted += 1
                except:
                    continue
            
            if deleted:
                self.logger.info("Cleaned %d logs", deleted)
        except Exception as e:
            self.logger.error("Cleanup error: %s", str(e))

# Safe instance creation
try:
    instance = LogCleaner()
except Exception as e:
    print(f"CRITICAL: Plugin failed to construct: {str(e)}")
    instance = None
