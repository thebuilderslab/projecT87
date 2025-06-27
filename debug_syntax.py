
#!/usr/bin/env python3
import ast
import sys

def check_syntax_detailed(filename):
    """Check syntax with detailed error reporting"""
    try:
        with open(filename, 'r') as f:
            source = f.read()
        
        # Try to parse the AST
        ast.parse(source, filename)
        print(f"✅ {filename}: Syntax OK")
        return True
        
    except SyntaxError as e:
        print(f"❌ {filename}: Syntax Error")
        print(f"   Line {e.lineno}: {e.msg}")
        print(f"   Text: {e.text.strip() if e.text else 'N/A'}")
        
        # Show context around the error
        lines = source.split('\n')
        start = max(0, e.lineno - 3)
        end = min(len(lines), e.lineno + 2)
        
        print(f"\n   Context:")
        for i in range(start, end):
            marker = ">>>" if i + 1 == e.lineno else "   "
            print(f"   {marker} {i+1:3d}: {lines[i]}")
        
        return False
        
    except Exception as e:
        print(f"❌ {filename}: Other error: {e}")
        return False

if __name__ == "__main__":
    files_to_check = ['web_dashboard.py', 'arbitrum_testnet_agent.py']
    
    for file in files_to_check:
        check_syntax_detailed(file)
        print()
