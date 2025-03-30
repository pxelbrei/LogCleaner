# LogCleaner Plugin for Pwnagotchi

[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)  
![Python 3.7+](https://img.shields.io/badge/python-3.7+-green.svg)  
![Pwnagotchi 1.5.5+](https://img.shields.io/badge/pwnagotchi-1.5.5%2B-lightgrey)  
![SD Card: 64GB Supported](https://img.shields.io/badge/SD%20Card-64GB%20SanDisk%20Ultra-brightgreen)

Automatically manages log files to prevent storage bloat on Pwnagotchi devices. Perfect for resource-constrained systems like Raspberry Pi Zero.

## Features

- **Age-based cleanup**: Deletes logs older than configured days (default: 7)
- **Size-based cleanup**: Enforces maximum log storage (default: 10MB)
- **Real-time monitoring**: Displays current log size/status on Pwnagotchi UI
- **Warning system**: Visual alerts at 90% capacity
- **Low overhead**: Optimized for minimal CPU/SD card wear

## Compatibility

| Hardware/Software       | Status      | Notes                      |
|-------------------------|-------------|----------------------------|
| SanDisk Ultra 64GB      | ✅ Tested   | FAT32 formatted            |
| Raspberry Pi Zero W/WH  | ✅ Tested   | Official and Jay's forks   |
| Pwnagotchi v1.5.5+      | ✅ Stable   |                            |
| Jay's Fork v2.9.5.3+    | ✅ Stable   | Python 3.7+ required       |

## Installation

1. Copy the plugin:
   ```bash
   sudo cp logcleaner.py /usr/local/lib/python3.7/dist-packages/pwnagotchi/plugins/
