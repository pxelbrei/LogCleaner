#!/usr/bin/env python3
import os
import glob
import time
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.plugins import Plugin

class LogCleaner(Plugin):
    __author__ = 'pxelbrei'
    __version__ = '1.3.0'
    __license__ = 'GPLv3'
    __description__ = 'Log management without internet dependency'

    def __init__(self):
        super(LogCleaner, self).__init__()
        self.log_dir = "/var/log/pwnagotchi/"
        self.max_log_age_days = 7
        self.max_log_size_mb = 10
        self.pos_x = 0
        self.pos_y = 0
        self.storage_status = "OK"
        self.last_cleanup = 0
        self.cleanup_interval = 3600  # 1 Stunde in Sekunden

    def on_config_changed(self, config):
        self.max_log_age_days = config['main']['plugins']['logcleaner']['max_log_age_days']
        self.max_log_size_mb = config['main']['plugins']['logcleaner']['max_log_size_mb']
        self.pos_x = int(config['main']['plugins']['logcleaner'].get('pos_x', 0))
        self.pos_y = int(config['main']['plugins']['logcleaner'].get('pos_y', 0))
        self.cleanup_interval = int(config['main']['plugins']['logcleaner'].get('interval', 3600))

    def on_ui_setup(self, ui):
        final_x = self.pos_x if self.pos_x >= 0 else ui.width() + self.pos_x
        final_y = self.pos_y if self.pos_y >= 0 else ui.height() + self.pos_y
        
        ui.add_element('log_status', LabeledValue(
            color='black',
            label='logs:',
            value='-',
            position=(final_x, final_y),
            label_font=ui.get_font('Bold 7'),
            text_font=ui.get_font('7')
        ))

    def _clean_logs(self):
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return

        self.last_cleanup = now
        cutoff = now - (self.max_log_age_days * 86400)
        deleted = 0

        for log_file in glob.glob(os.path.join(self.log_dir, "*.log")):
            try:
                if os.path.getmtime(log_file) < cutoff:
                    os.remove(log_file)
                    deleted += 1
            except Exception as e:
                self.logger.warning(f"[LogCleaner] Delete failed: {e}")

        current_size = self._get_log_size_mb()
        while current_size > self.max_log_size_mb:
            oldest = min(glob.glob(os.path.join(self.log_dir, "*.log")), key=os.path.getmtime)
            try:
                current_size -= os.path.getsize(oldest) / (1024 ** 2)
                os.remove(oldest)
                deleted += 1
            except Exception as e:
                self.logger.error(f"[LogCleaner] Size cleanup failed: {e}")
                break

        return deleted

    def on_second(self, agent):
        # Jede Sekunde prüfen, aber nur stündlich bereinigen
        self._update_status()

    def _update_status(self):
        current_size = self._get_log_size_mb()
        
        if current_size > self.max_log_size_mb * 0.9:
            self.storage_status = "WARN"
        elif current_size > self.max_log_size_mb:
            self.storage_status = "FULL!"
        else:
            self.storage_status = "OK"

        # Stündliche Bereinigung
        if int(time.time()) % self.cleanup_interval == 0:
            deleted = self._clean_logs()
            if deleted:
                self.logger.info(f"[LogCleaner] Cleaned {deleted} files")

    def _get_log_size_mb(self):
        try:
            return sum(os.path.getsize(f) for f in glob.glob(os.path.join(self.log_dir, "*.log"))) / (1024 ** 2)
        except Exception as e:
            self.logger.error(f"[LogCleaner] Size check error: {e}")
            return 0

    def on_ui_update(self, ui):
        ui.set('log_status', f"{self._get_log_size_mb():.1f}MB/{self.storage_status}")

instance = LogCleaner()
