#!/usr/bin/env python3
import os
import glob
import time
import logging
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'pxelbrei'
    __version__ = '1.5.7'
    __license__ = 'GPLv3'
    __description__ = 'Working UI version with font fixes'

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Initialize logging
        try:
            os.makedirs('/var/log/pwnagotchi/', exist_ok=True)
            handler = logging.FileHandler('/var/log/pwnagotchi/logcleaner.log')
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
        except Exception as e:
            console_handler = logging.StreamHandler()
            self.logger.addHandler(console_handler)
            self.logger.error("File logging failed: %s", str(e))

        # Default configuration
        self.log_dir = "/etc/pwnagotchi/log/"
        self.max_log_age_days = 7
        self.max_log_size_mb = 10
        self.pos_x = 180
        self.pos_y = 50
        self.text_color = 'black'
        self.cleanup_interval = 1800
        self.storage_status = "OK"
        self.last_cleanup = 0

        self.logger.info("Plugin initialized (v%s)", self.__version__)

    def on_loaded(self):
        """Called when plugin is loaded"""
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            self.logger.info("Plugin loaded successfully")
        except Exception as e:
            self.logger.error("Load failed: %s", str(e))

    def on_ui_setup(self, ui):
        """Initialize UI elements with font fallbacks"""
        try:
            # Font fallback solution
            fonts = {
                'label': getattr(ui, 'BOLD_FONT', ('Bold', 8, False)),
                'text': getattr(ui, 'SMALL_FONT', ('Small', 8, False))
            }
            
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
            self.logger.info("UI setup complete at (%d,%d)", self.pos_x, self.pos_y)
        except Exception as e:
            self.logger.error("UI setup failed: %s", str(e), exc_info=True)

    def on_ui_update(self, ui):
        """Update display"""
        try:
            current_size = self._get_log_size_mb()
            ui.set('log_status', f"{current_size:.1f}MB/{self.storage_status}")
        except Exception as e:
            self.logger.error("UI update failed: %s", str(e))

    def _get_log_files(self):
        """Get sorted log files"""
        try:
            return sorted(glob.glob(os.path.join(self.log_dir, "*.log")), key=os.path.getmtime)
        except Exception as e:
            self.logger.error("File scan failed: %s", str(e))
            return []

    def _get_log_size_mb(self):
        """Calculate total log size in MB"""
        try:
            return sum(os.path.getsize(f) for f in self._get_log_files()) / (1024 ** 2)
        except Exception as e:
            self.logger.error("Size calc failed: %s", str(e))
            return 0

    def on_second(self, agent):
        """Handle periodic tasks"""
        try:
            # Update status
            current_size = self._get_log_size_mb()
            self.storage_status = (
                "FULL!" if current_size > self.max_log_size_mb else
                "WARN" if current_size > self.max_log_size_mb * 0.9 else
                "OK"
            )
            
            # Run cleanup on interval
            if time.time() - self.last_cleanup >= self.cleanup_interval:
                self._clean_logs()
                self.last_cleanup = time.time()
        except Exception as e:
            self.logger.error("Cycle error: %s", str(e))

    def _clean_logs(self):
        """Execute cleanup"""
        try:
            deleted = 0
            cutoff = time.time() - (self.max_log_age_days * 86400)
            
            # Age cleanup
            for log_file in self._get_log_files():
                if os.path.getmtime(log_file) < cutoff:
                    try:
                        os.remove(log_file)
                        deleted += 1
                    except Exception as e:
                        self.logger.warning("Delete failed: %s", str(e))
            
            # Size cleanup
            while self._get_log_size_mb() > self.max_log_size_mb:
                oldest = next(iter(self._get_log_files()), None)
                if oldest and os.path.exists(oldest):
                    try:
                        os.remove(oldest)
                        deleted += 1
                    except Exception as e:
                        self.logger.error("Remove failed: %s", str(e))
                        break
            
            if deleted > 0:
                self.logger.info("Deleted %d log files", deleted)
        except Exception as e:
            self.logger.error("Cleanup failed: %s", str(e), exc_info=True)

# Plugin instance
def create_instance():
    return LogCleaner()

instance = create_instance()
