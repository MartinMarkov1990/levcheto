#!c:\Marto\levcheto\flask\Scripts\python.exe
# EASY-INSTALL-ENTRY-SCRIPT: 'sqlalchemy-migrate==0.9.6','console_scripts','migrate'
__requires__ = 'sqlalchemy-migrate==0.9.6'
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point('sqlalchemy-migrate==0.9.6', 'console_scripts', 'migrate')()
    )
