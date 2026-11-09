#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Build the Apps menu from executables available in this userspace."""
import os
import shutil
import sys
import xml.etree.ElementTree as ET

source, destination = sys.argv[1:]
browser = os.environ.get('ASUS_BROWSER', 'netsurf')
if browser not in ('netsurf', 'firefox-esr'):
    raise SystemExit('ASUS_BROWSER must be netsurf or firefox-esr')
tree = ET.parse(source)
menu = tree.getroot().find('RootMenu')
if menu is None:
    raise SystemExit('JWM template has no RootMenu')
if shutil.which(browser):
    ET.SubElement(menu, 'Program', label='Browser').text = '/usr/local/bin/asus-goodix-browser'
keyboards = ('svkbd-mobile-intl', 'svkbd-mobile', 'svkbd-mobile-plain', 'svkbd-en', 'matchbox-keyboard')
if any(shutil.which(name) for name in keyboards):
    ET.SubElement(menu, 'Program', label='Keyboard').text = '/usr/local/bin/asus-goodix-keyboard'
tree.write(destination, encoding='utf-8', xml_declaration=True)
