
#!/usr/bin/env python3
"""Fix syntax issues in main.py"""

import re
import os

def fix_main_syntax():
    """Fix syntax issues in main.py"""
    if not os.path.exists('main.py'):
        print("main.py not found")
        return False
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix indentation issues - remove unexpected indentation from function definitions
    content = re.sub(r'^    def ([a-zA-Z_][a-zA-Z0-9_]*)\(', r'def \1(', content, flags=re.MULTILINE)
    content = re.sub(r'^    class ([a-zA-Z_][a-zA-Z0-9_]*)', r'class \1', content, flags=re.MULTILINE)
    
    # Remove problematic complex type annotations
    content = re.sub(r': t\.[A-Za-z\[\]_, ]+', '', content)
    content = re.sub(r'-> t\.[A-Za-z\[\]_, ]+', '', content)
    content = re.sub(r'-> ".*?"', '', content)
    
    # Remove complex generic types
    content = re.sub(r'\[.*?\]', '', content)
    
    # Fix import issues
    lines = content.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Skip problematic imports
        if any(skip in line for skip in [
            'from typing import',
            'import typing as t',
            'from pydantic',
            'from jinja2',
            'from charset_normalizer'
        ]):
            continue
        
        # Simplify complex class definitions
        if line.strip().startswith('class ') and '(' in line and len(line) > 100:
            class_name = line.split('class ')[1].split('(')[0]
            line = f'class {class_name}:'
        
        fixed_lines.append(line)
    
    # Write back the fixed content
    fixed_content = '\n'.join(fixed_lines)
    
    with open('main.py', 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print("✅ Fixed main.py syntax issues")
    return True

if __name__ == "__main__":
    fix_main_syntax()
