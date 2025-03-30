#!/usr/bin/env python3
import os
import glob
import time
import logging
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'pxelbrei'
    __version__ = '1.5.5'
    __license__ = 'GPLv3'
    __description__ = 'Stable log management with color customization'

    def __init__(self):
        super(LogCleaner, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Safe initialization
        try:
            os.makedirs("/var/log/pwnagotchi/", exist_ok=True)
            handler = logging.FileHandler("/var/log/pwnagotchi/logcleaner.log")
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
        except:
            handler = logging.StreamHandler()
            self.logger.addHandler(handler)

        # Safe defaults
        self.log_dir = "/etc/pwnagotchi/log/"
        self.max_log_age_days = 7
        self.max_log_size_mb = 10
        self.pos_x = 180
        self.pos_y = 50
        self.text_color = 'black'
        self.cleanup_interval = 1800
        self.storage_status = "OK"
        self.last_cleanup = 0
        self.last_ui_update = 0

    def on_loaded(self):
        self.logger.info("Plugin successfully loaded (v%s)", self.__version__)
        os.makedirs(self.log_dir, exist_ok=True)

    def on_config_changed(self, config):
        try:
            # Required parameters
            self.log_dir = str(config['main']['plugins']['logcleaner']['log_dir'])
            self.max_log_age_days = int(config['main']['plugins']['logcleaner']['max_log_age_days'])
            self.max_log_size_mb = int(config['main']['plugins']['logcleaner']['max_log_size_mb'])
            
            # Optional parameters with defaults
            self.pos_x = int(config['main']['plugins']['logcleaner'].get('pos_x', 180))
            self.pos_y = int(config['main']['plugins']['logcleaner'].get('pos_y', 50))
            self.cleanup_interval = int(config['main']['plugins']['logcleaner'].get('interval', 1800))
            
            # Color handling
            color = str(config['main']['plugins']['logcleaner'].get('text_color', 'black')).lower()
            self.text_color = color if color in ('black', 'white') else 'black'
            
            self.logger.info("Configuration loaded (color: %s)", self.text_color)
        except Exception as e:
            self.logger.error("Config error: %s", str(e))

    def on_ui_setup(self, ui):
        try:
            # Font fallback handling
            fonts = {
                'bold': getattr(ui, 'BOLD_FONT', None),
                'small': getattr(ui, 'SMALL_FONT', None)
            }
            
            ui.add_element(
                'log_status',
                LabeledValue(
                    color=self.text_color,
                    label='LOGS:',
                    value='0.0MB/OK',
                    position=(self.pos_x, self.pos_y),
                    label_font=fonts['bold'],
                    text_font=fonts['small']
                )
            )
            self.logger.info("Display initialized at (%d,%d) color: %s", 
                           self.pos_x, self.pos_y, self.text_color)
        except Exception as e:
            self.logger.error("Display setup failed: %s", str(e))

    def on_ui_update(self, ui):
        try:
            current_size = self._get_log_size_mb()
            ui.set('log_status', f"{current_size:.1f}MB/{self.storage_status}")
        except Exception as e:
            self.logger.error("Display update failed: %s", str(e))

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
        try:
            # Status update
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
            self.logger.error("Cycle error: %s", str(e))

    def _clean_logs(self):
        try:
            deleted = 0
            cutoff = time.time() - (self.max_log_age_days * 86400)
            
            # Age cleanup
            for log_file in self._get_log_files():
                if os.path.getmtime(log_file) < cutoff:
                    try:
                        os.remove(log_file)
                        deleted += 1
                    except:
                        pass
            
            # Size cleanup
            while self._get_log_size_mb() > self.max_log_size_mb:
                oldest = next(iter(self._get_log_files()), None)
                if oldest and os.path.exists(oldest):
                    os.remove(oldest)
                    deleted += 1
            
            if deleted > 0:
                self.logger.info("Cleaned %d files", deleted)
        except Exception as e:
            self.logger.error("Cleanup error: %s", str(e))

# Plugin instance (critical for proper loading)
instance = LogCleaner()
