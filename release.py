#!/usr/bin/env python3
# Create a release zip
import zipfile
from datetime import datetime
from pds import PDS_VERSION

with zipfile.ZipFile(f'pds-{PDS_VERSION}.zip', 'w') as zipf:
    for file in ['pds.py', 'pds', 'pds.bat', 'LICENSE', 'README.md']:
        zipf.write(file, f'pds/{file}')
