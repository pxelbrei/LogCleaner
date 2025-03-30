#!/usr/bin/env python3
import os
import glob
import time
import logging
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'p.xelbrei'
    __version__ = '1.5.4'
    __license__ = 'GPLv3'
    __description__ = 'Log management with customizable text color'

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
        self.pos_x = 180
        self.pos_y = 50
        self.text_color = 'black'  # Default text color
        self.cleanup_interval = 1800
        self.storage_status = "OK"
        self.last_cleanup = 0
        self.last_ui_update = 0
        
        os.makedirs(self.log_dir, exist_ok=True)
        self.logger.info("Plugin initialized (v%s)", self.__version__)

    def on_config_changed(self, config):
        """Load all configurable parameters"""
        try:
            # Load standard config
            self.log_dir = config['main']['plugins']['logcleaner'].get('log_dir', "/etc/pwnagotchi/log/")
            self.max_log_age_days = int(config['main']['plugins']['logcleaner'].get('max_log_age_days', 7))
            self.max_log_size_mb = int(config['main']['plugins']['logcleaner'].get('max_log_size_mb', 10))
            self.pos_x = int(config['main']['plugins']['logcleaner'].get('pos_x', 180))
            self.pos_y = int(config['main']['plugins']['logcleaner'].get('pos_y', 50))
            self.cleanup_interval = int(config['main']['plugins']['logcleaner'].get('interval', 1800))
            
            # New: Load text color config
            self.text_color = config['main']['plugins']['logcleaner'].get('text_color', 'black').lower()
            if self.text_color not in ('black', 'white'):
                self.text_color = 'black'
                self.logger.warning("Invalid text_color, using default (black)")
            
            self.logger.info("Config loaded: color=%s", self.text_color)
            
        except Exception as e:
            self.logger.error("Config error: %s", str(e), exc_info=True)

    def on_ui_setup(self, ui):
        """Initialize UI with configurable color"""
        try:
            # Use available font constants
            label_font = ui.BOLD_FONT if hasattr(ui, 'BOLD_FONT') else None
            text_font = ui.SMALL_FONT if hasattr(ui, 'SMALL_FONT') else None
            
            ui.add_element(
                'log_status',
                LabeledValue(
                    color=self.text_color,  # Use configured color
                    label='LOGS:',
                    value='0.0MB/OK',
                    position=(self.pos_x, self.pos_y),
                    label_font=label_font,
                    text_font=text_font
                )
            )
            self.logger.info("UI element added (color: %s, pos: %d,%d)", 
                           self.text_color, self.pos_x, self.pos_y)
        except Exception as e:
            self.logger.error("UI setup failed: %s", str(e), exc_info=True)

    # [Keep all other methods unchanged from previous version...]

# Plugin instance
instance = LogCleaner()
