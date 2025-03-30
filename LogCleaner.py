#!/usr/bin/env python3
import os
import glob
import time
import logging
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'pxelbrei'
    __version__ = '1.5.8'
    __license__ = 'GPLv3'
    __description__ = 'Stable log management without bootloops'

    def __init__(self):
        # Minimalistische Initialisierung
        super().__init__()
        self._ready = False
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Console logging only during init
        console_handler = logging.StreamHandler()
        self.logger.addHandler(console_handler)
        self.logger.info("Initializing plugin (v%s)", self.__version__)

    def on_loaded(self):
        """Safe delayed initialization"""
        try:
            # Config defaults
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
            
            # Ensure log directory exists
            os.makedirs(self.log_dir, exist_ok=True)
            
            self._ready = True
            self.logger.info("Plugin fully loaded and ready")
        except Exception as e:
            self.logger.error("Load failed: %s", str(e))
            raise

    def on_config_changed(self, config):
        if not self._ready:
            return
            
        try:
            # Safely load config
            self.log_dir = str(config['main']['plugins']['logcleaner'].get('log_dir', "/etc/pwnagotchi/log/"))
            self.max_log_age_days = int(config['main']['plugins']['logcleaner'].get('max_log_age_days', 7))
            self.max_log_size_mb = int(config['main']['plugins']['logcleaner'].get('max_log_size_mb', 10))
            self.pos_x = int(config['main']['plugins']['logcleaner'].get('pos_x', 150))
            self.pos_y = int(config['main']['plugins']['logcleaner'].get('pos_y', 30))
            self.text_color = str(config['main']['plugins']['logcleaner'].get('text_color', 'black')).lower()
            self.cleanup_interval = int(config['main']['plugins']['logcleaner'].get('interval', 3600))
            
            self.logger.info("New config loaded")
        except Exception as e:
            self.logger.error("Config error: %s", str(e))

    def on_ui_setup(self, ui):
        if not self._ready:
            return
            
        try:
            # Ultra-safe font handling
            font_specs = {
                'label': ('Bold', 8, False),
                'text': ('Small', 8, False)
            }
            
            ui.add_element(
                'log_status',
                LabeledValue(
                    color=self.text_color,
                    label='LOGS:',
                    value='0.0MB/OK',
                    position=(self.pos_x, self.pos_y),
                    label_font=font_specs['label'],
                    text_font=font_specs['text']
                )
            )
            self.logger.info("UI setup complete")
        except Exception as e:
            self.logger.error("UI setup failed: %s", str(e))

    def on_ui_update(self, ui):
        if not self._ready:
            return
            
        try:
            current_size = self._get_log_size_mb()
            ui.set('log_status', f"{current_size:.1f}MB/{self.storage_status}")
        except Exception as e:
            self.logger.error("UI update failed: %s", str(e))

    def _get_log_files(self):
        try:
            return sorted(glob.glob(os.path.join(self.log_dir, "*.log")), key=os.path.getmtime)
        except:
            return []

    def _get_log_size_mb(self):
        try:
            return sum(os.path.getsize(f) for f in self._get_log_files()) / (1024 ** 2)
        except:
            return 0

    def on_second(self, agent):
        if not self._ready:
            return
            
        try:
            current_size = self._get_log_size_mb()
            self.storage_status = (
                "FULL!" if current_size > self.max_log_size_mb else
                "WARN" if current_size > self.max_log_size_mb * 0.9 else
                "OK"
            )
            
            if time.time() - self.last_cleanup >= self.cleanup_interval:
                self._clean_logs()
                self.last_cleanup = time.time()
        except Exception as e:
            self.logger.error("Cycle error: %s", str(e))

    def _clean_logs(self):
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
                self.logger.info("Deleted %d logs", deleted)
        except Exception as e:
            self.logger.error("Cleanup error: %s", str(e))

# Safe instance creation
instance = None
try:
    instance = LogCleaner()
except Exception as e:
    print(f"CRITICAL: Plugin failed to initialize: {str(e)}")
