# LogCleaner Plugin for Pwnagotchi

[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)  

Automatically manages log files to prevent storage bloat on Pwnagotchi devices. Perfect for resource-constrained systems like Raspberry Pi Zero.

## Features

- **Age-based cleanup**: Deletes logs older than configured days (default: 7)
- **Size-based cleanup**: Enforces maximum log storage (default: 10MB)
- **Real-time monitoring**: Displays current log size/status on Pwnagotchi UI
- **Warning system**: Visual alerts at 90% capacity
- **Low overhead**: Optimized for minimal CPU/SD card wear

## 🔧 How It Works

### Core Functionality
This plugin implements a **dual-cleanup system** to manage log files:

```mermaid
graph TD
    A[Check Logs] --> B{Age >7 days?}
    B -->|Yes| C[Delete File]
    B -->|No| D{Size >10MB?}
    D -->|Yes| E[Delete Oldest]
    D -->|No| F[Keep File]

sequenceDiagram
    participant Pwnagotchi
    participant Plugin
    participant SD_Card
    
    Pwnagotchi->>Plugin: Internet available
    Plugin->>SD_Card: Scan /var/log/pwnagotchi/
    SD_Card->>Plugin: Return file list
    Plugin->>Plugin: Calculate total size
    alt Size >10MB or Age >7d
        Plugin->>SD_Card: Delete target files
    end
    Plugin->>Pwnagotchi: Update UI status

/var/log/pwnagotchi/
├── pwnagotchi.log       # Active log (never deleted)
├── pwnagotchi.1.log     # Older logs (cleaned by plugin)
└── pwnagotchi.2.log     # Older logs (cleaned by plugin)

# Check permissions
ls -la /var/log/pwnagotchi*

# Manual cleanup test
sudo python3 -c "import os, time; [os.remove(f) for f in ['/var/log/pwnagotchi/'+f for f in os.listdir('/var/log/pwnagotchi/')] if time.time()-os.path.getmtime(f) > 604800]"
