#!/usr/bin/env python3
"""Script to remove all inline keyboards from dashboard.py"""

import re

file_path = r'c:\Users\prava\OneDrive\Desktop\Primium bot\src\handlers\dashboard.py'

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to match reply_markup=InlineKeyboardMarkup(inline_keyboard=[...]) including the closing ])\n
# This regex matches the entire inline keyboard block
pattern = r',\s*reply_markup=InlineKeyboardMarkup\(inline_keyboard=\[[^\]]*\]\)'

# Replace all occurrences with empty string
new_content = re.sub(pattern, '', content)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully removed all inline keyboards from dashboard.py!")
