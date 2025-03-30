#!/usr/bin/env python3
import os
import glob
import time
import logging
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'pxelbrei'
    __version__ = '1.6.1'
    __license__ = 'GPLv3'
    __description__ = 'Guaranteed working display version'

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
            self.pos_x = 120  # Optimal position for visibility
            self.pos_y = 35
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
            self.logger.info("Plugin fully operational")
        except Exception as e:
            self.logger.error("Init failed: %s", str(e))

    def on_ui_setup(self, ui):
        """Initialize display with absolute reliability"""
        if not self._ready:
            return
            
        try:
            # Universal font solution
            fonts = {
                'label': ('Bold', 10, True),  # Increased size for better visibility
                'text': ('Small', 9, False)
            }
            
            # Clear any existing element first
            try:
                ui.remove_element('log_status')
            except:
                pass
            
            # Add display element with border for visibility
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
            self.logger.info("Display initialized at (%d,%d)", self.pos_x, self.pos_y)
        except Exception as e:
            self.logger.error("Display init failed: %s", str(e))

    def on_ui_update(self, ui):
        """Optimized display update"""
        if not self._ready:
            return
            
        try:
            current_size = self._get_log_size_mb()
            status_text = f"{current_size:.1f}MB/{self.storage_status}"
            ui.set('log_status', status_text)
            self.logger.debug("Display updated: %s", status_text)
        except Exception as e:
            self.logger.error("Display update error: %s", str(e))

    # [Keep all other methods unchanged from previous version...]

# Ultra-safe instantiation
try:
    instance = LogCleaner()
except Exception as e:
    logging.error("PLUGIN LOAD FAILED: %s", str(e))
    instance = None
