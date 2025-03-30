#!/usr/bin/env python3
import os
import glob
import time
import logging
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'p.xelbrei'
    __version__ = '1.5.0'
    __license__ = 'GPLv3'
    __description__ = 'Enhanced log management with detailed activity logging'

    def __init__(self):
        Plugin.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Log-Handler für Dateiausgabe
        handler = logging.FileHandler('/var/log/pwnagotchi/logcleaner.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        self.log_dir = "/etc/pwnagotchi/log/"
        self.max_log_age_days = 7
        self.max_log_size_mb = 10
        self.pos_x = 0
        self.pos_y = 0
        self.storage_status = "OK"
        self.last_cleanup = 0
        self.cleanup_interval = 3600
        
        os.makedirs(self.log_dir, exist_ok=True)
        self.logger.info("Plugin initialized | Version %s", self.__version__)
        self.logger.info("Log directory: %s", self.log_dir)

    def on_loaded(self):
        self.logger.info("Plugin loaded successfully")
        self.logger.info("Configuration: max_age=%d days, max_size=%d MB, interval=%d sec", 
                        self.max_log_age_days, self.max_log_size_mb, self.cleanup_interval)

    def on_unload(self, ui):
        self.logger.info("Plugin unloaded - cleaning up UI elements")
        try:
            ui.remove_element('log_status')
            self.logger.info("UI elements removed successfully")
        except Exception as e:
            self.logger.error("Failed to remove UI elements: %s", str(e))

    def on_config_changed(self, config):
        try:
            old_dir = self.log_dir
            self.log_dir = config['main']['plugins']['logcleaner'].get('log_dir', "/etc/pwnagotchi/log/")
            self.log_dir = os.path.join(self.log_dir, '')
            
            if old_dir != self.log_dir:
                self.logger.info("Log directory changed from %s to %s", old_dir, self.log_dir)
            
            # Restliche Konfiguration...
            self.logger.debug("Config reloaded successfully")
            
        except Exception as e:
            self.logger.error("Config error: %s", str(e), exc_info=True)

    def _clean_logs(self):
        start_time = time.time()
        self.logger.info("Starting cleanup cycle")
        
        try:
            # Altersbereinigung
            deleted_age = 0
            cutoff = time.time() - (self.max_log_age_days * 86400)
            for log_file in self._get_log_files():
                if os.path.getmtime(log_file) < cutoff:
                    try:
                        os.remove(log_file)
                        deleted_age += 1
                        self.logger.debug("Deleted old file: %s", os.path.basename(log_file))
                    except Exception as e:
                        self.logger.warning("Failed to delete %s: %s", log_file, str(e))
            
            # Größenbereinigung
            deleted_size = 0
            current_size = self._get_log_size_mb()
            while current_size > self.max_log_size_mb:
                oldest = self._get_log_files()[0]
                try:
                    file_size = os.path.getsize(oldest) / (1024 ** 2)
                    os.remove(oldest)
                    current_size -= file_size
                    deleted_size += 1
                    self.logger.debug("Deleted large file: %s (%.2f MB)", os.path.basename(oldest), file_size)
                except Exception as e:
                    self.logger.error("Size cleanup failed: %s", str(e))
                    break
            
            duration = time.time() - start_time
            self.logger.info(
                "Cleanup completed in %.2f sec | Deleted: %d by age, %d by size | Remaining: %.2f MB",
                duration, deleted_age, deleted_size, current_size
            )
            return deleted_age + deleted_size
            
        except Exception as e:
            self.logger.error("Cleanup failed: %s", str(e), exc_info=True)
            return 0

    def on_second(self, agent):
        try:
            # Statusaktualisierung
            current_size = self._get_log_size_mb()
            new_status = (
                "FULL!" if current_size > self.max_log_size_mb else
                "WARN" if current_size > self.max_log_size_mb * 0.9 else
                "OK"
            )
            
            if new_status != self.storage_status:
                self.logger.info(
                    "Storage status changed: %s -> %s (%.2f MB/%.2f MB)",
                    self.storage_status, new_status, current_size, self.max_log_size_mb
                )
                self.storage_status = new_status
            
            # Zeitgesteuerte Bereinigung
            if time.time() - self.last_cleanup >= self.cleanup_interval:
                self._clean_logs()
                self.last_cleanup = time.time()
                
        except Exception as e:
            self.logger.error("Second update failed: %s", str(e))

# [Rest des Codes bleibt gleich...]
