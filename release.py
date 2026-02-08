#!/usr/bin/env python3
# Create a release zip
import zipfile
from datetime import datetime

with zipfile.ZipFile(f'pds-{datetime.now().strftime("%Y%m%d")}.zip', 'w') as zipf:
    for file in ['pds.py', 'pds', 'pds.bat', 'LICENSE', 'README.md']:
        zipf.write(file, f'pds/{file}')
