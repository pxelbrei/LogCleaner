#!/usr/bin/env python3
import os
import glob
import time
import logging
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'pxelbrei'
    __version__ = '1.5.6'
    __license__ = 'GPLv3'
    __description__ = 'Fixed initialization log management plugin'

    def __init__(self):
        # Korrekte Super-Klassen-Initialisierung
        super().__init__()  # Vereinfachte Python3-Syntax
        
        # Logger-Initialisierung
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Fallback-Logging wenn Dateilogging fehlschlägt
        try:
            os.makedirs('/var/log/pwnagotchi/', exist_ok=True)
            file_handler = logging.FileHandler('/var/log/pwnagotchi/logcleaner.log')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
        except Exception as e:
            console_handler = logging.StreamHandler()
            self.logger.addHandler(console_handler)
            self.logger.error("File logging failed, using console: %s", str(e))

        # Standardwerte
        self.log_dir = "/etc/pwnagotchi/log/"
        self.max_log_age_days = 7
        self.max_log_size_mb = 10
        self.pos_x = 180
        self.pos_y = 50
        self.text_color = 'black'
        self.cleanup_interval = 1800
        self.storage_status = "OK"
        self.last_cleanup = 0

        self.logger.info("LogCleaner plugin initialized (v%s)", self.__version__)

    def on_loaded(self):
        """Wird aufgerufen wenn das Plugin geladen wird"""
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            self.logger.info("Plugin loaded with config: dir=%s, age=%dd, size=%dMB", 
                           self.log_dir, self.max_log_age_days, self.max_log_size_mb)
        except Exception as e:
            self.logger.error("Load failed: %s", str(e))

    def on_config_changed(self, config):
        """Konfigurationsänderungen verarbeiten"""
        try:
            # Pflichtparameter
            self.log_dir = str(config['main']['plugins']['logcleaner']['log_dir'])
            self.max_log_age_days = int(config['main']['plugins']['logcleaner']['max_log_age_days'])
            self.max_log_size_mb = int(config['main']['plugins']['logcleaner']['max_log_size_mb'])
            
            # Optionale Parameter
            self.pos_x = int(config['main']['plugins']['logcleaner'].get('pos_x', 180))
            self.pos_y = int(config['main']['plugins']['logcleaner'].get('pos_y', 50))
            self.text_color = str(config['main']['plugins']['logcleaner'].get('text_color', 'black')).lower()
            self.cleanup_interval = int(config['main']['plugins']['logcleaner'].get('interval', 1800))
            
            self.logger.info("New config loaded: color=%s, pos=(%d,%d)", 
                           self.text_color, self.pos_x, self.pos_y)
        except Exception as e:
            self.logger.error("Config error: %s", str(e))

    def on_ui_setup(self, ui):
        """UI-Elemente initialisieren"""
        try:
            ui.add_element(
                'log_status',
                LabeledValue(
                    color=self.text_color,
                    label='LOGS:',
                    value='0.0MB/OK',
                    position=(self.pos_x, self.pos_y),
                    label_font=ui.BOLD_FONT,
                    text_font=ui.SMALL_FONT
                )
            )
            self.logger.info("Display setup complete at (%d,%d)", self.pos_x, self.pos_y)
        except Exception as e:
            self.logger.error("UI setup failed: %s", str(e))

    # [Weitere Methoden wie zuvor...]

# Plugin-Instanz KORREKT initialisieren
def create_plugin_instance():
    return LogCleaner()

instance = create_plugin_instance()
