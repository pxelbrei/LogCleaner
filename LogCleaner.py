#!/usr/bin/env python3
import os
import glob
import time
import logging
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'pxelbrei'
    __version__ = '1.5.1'
    __license__ = 'GPLv3'
    __description__ = 'Robust log management with enhanced error handling'

    def __init__(self):
        Plugin.__init__(self)
        
        # Initialize logger first
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Ensure log directory exists before creating handler
        self._init_logging()
        
        # Configuration defaults
        self.log_dir = "/etc/pwnagotchi/log/"
        self.max_log_age_days = 7
        self.max_log_size_mb = 10
        self.pos_x = 0
        self.pos_y = 0
        self.storage_status = "OK"
        self.last_cleanup = 0
        self.cleanup_interval = 3600
        
        # Create working directories
        os.makedirs(self.log_dir, exist_ok=True)
        self.logger.info("Plugin initialized (v%s)", self.__version__)

    def _init_logging(self):
        """Initialize logging with proper directory structure"""
        log_dir = "/var/log/pwnagotchi/"
        log_file = os.path.join(log_dir, "logcleaner.log")
        
        try:
            os.makedirs(log_dir, exist_ok=True)
            handler = logging.FileHandler(log_file)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
        except Exception as e:
            # Fallback to console logging if file logging fails
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            self.logger.addHandler(console_handler)
            self.logger.error("Failed to initialize file logging: %s", str(e))

    def on_loaded(self):
        """Called when plugin is loaded"""
        self.logger.info("Plugin loaded with config: age=%dd, size=%dMB, interval=%ds", 
                        self.max_log_age_days, self.max_log_size_mb, self.cleanup_interval)

    def on_unload(self, ui):
        """Called when plugin is unloaded"""
        try:
            ui.remove_element('log_status')
            self.logger.info("Plugin unloaded successfully")
        except Exception as e:
            self.logger.error("Failed to unload: %s", str(e))

    def on_config_changed(self, config):
        """Handle configuration changes"""
        try:
            new_dir = config['main']['plugins']['logcleaner'].get('log_dir', "/etc/pwnagotchi/log/")
            new_dir = os.path.join(new_dir, '')
            
            if new_dir != self.log_dir:
                self.logger.info("Log directory changed to: %s", new_dir)
                os.makedirs(new_dir, exist_ok=True)
                self.log_dir = new_dir
                
        except Exception as e:
            self.logger.error("Config error: %s", str(e), exc_info=True)

    def _get_log_files(self):
        """Get sorted list of log files"""
        try:
            files = glob.glob(os.path.join(self.log_dir, "*.log"))
            return sorted(files, key=os.path.getmtime)
        except Exception as e:
            self.logger.error("Failed to list logs: %s", str(e))
            return []

    def _get_log_size_mb(self):
        """Calculate total log size in MB"""
        try:
            size_bytes = sum(os.path.getsize(f) for f in self._get_log_files())
            return size_bytes / (1024 ** 2)
        except Exception as e:
            self.logger.error("Size calculation failed: %s", str(e))
            return 0

    def _clean_logs(self):
        """Execute cleanup procedure"""
        self.logger.info("Starting cleanup cycle")
        deleted = 0
        
        try:
            # Age-based cleanup
            cutoff = time.time() - (self.max_log_age_days * 86400)
            for log_file in self._get_log_files():
                try:
                    if os.path.getmtime(log_file) < cutoff:
                        os.remove(log_file)
                        deleted += 1
                        self.logger.debug("Deleted (age): %s", os.path.basename(log_file))
                except Exception as e:
                    self.logger.warning("Delete failed: %s - %s", log_file, str(e))

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
                    self.logger.debug("Deleted (size): %s (%.2fMB)", os.path.basename(oldest), file_size)
                except Exception as e:
                    self.logger.error("Size cleanup failed: %s", str(e))
                    break

            self.logger.info("Cleanup completed. Deleted %d files. Current size: %.2fMB", deleted, current_size)
            return deleted
            
        except Exception as e:
            self.logger.error("Cleanup failed: %s", str(e), exc_info=True)
            return 0

    def on_second(self, agent):
        """Handle periodic tasks"""
        try:
            # Update status
            current_size = self._get_log_size_mb()
            new_status = "FULL!" if current_size > self.max_log_size_mb else \
                        "WARN" if current_size > self.max_log_size_mb * 0.9 else \
                        "OK"
            
            if new_status != self.storage_status:
                self.logger.info("Storage status changed: %s → %s (%.2fMB/%.2fMB)", 
                               self.storage_status, new_status, current_size, self.max_log_size_mb)
                self.storage_status = new_status
            
            # Run cleanup on interval
            if time.time() - self.last_cleanup >= self.cleanup_interval:
                self._clean_logs()
                self.last_cleanup = time.time()
                
        except Exception as e:
            self.logger.error("Periodic update failed: %s", str(e))

    def on_ui_update(self, ui):
        """Update UI display"""
        try:
            ui.set('log_status', f"{self._get_log_size_mb():.1f}MB/{self.storage_status}")
        except Exception as e:
            self.logger.error("UI update failed: %s", str(e))

# Plugin instance (must be at module level)
instance = LogCleaner()
