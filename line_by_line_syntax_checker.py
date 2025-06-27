
#!/usr/bin/env python3
"""
Line-by-line syntax checker for web_dashboard.py
"""
import ast
import sys

def check_web_dashboard_syntax():
    """Check web_dashboard.py for syntax errors line by line"""
    print("🔍 LINE-BY-LINE SYNTAX SCAN: web_dashboard.py")
    print("=" * 60)
    
    try:
        with open('web_dashboard.py', 'r') as f:
            lines = f.readlines()
        
        print(f"📄 Total lines: {len(lines)}")
        print("🔍 Scanning for syntax errors...\n")
        
        # Try to compile the entire file first
        try:
            with open('web_dashboard.py', 'r') as f:
                source = f.read()
            ast.parse(source, 'web_dashboard.py')
            print("✅ Overall syntax check: PASSED")
        except SyntaxError as e:
            print(f"❌ Overall syntax check: FAILED")
            print(f"   Error at line {e.lineno}: {e.msg}")
            print(f"   Text: {e.text.strip() if e.text else 'N/A'}")
            
            # Show detailed context around the error
            if e.lineno:
                start = max(1, e.lineno - 3)
                end = min(len(lines), e.lineno + 3)
                print(f"\n📍 CONTEXT AROUND LINE {e.lineno}:")
                for i in range(start - 1, end):
                    marker = ">>> " if i + 1 == e.lineno else "    "
                    print(f"{marker}{i+1:3d}: {lines[i].rstrip()}")
        
        # Check for common syntax issues line by line
        print(f"\n🔍 DETAILED LINE ANALYSIS:")
        issues_found = []
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for indentation issues
            if line_stripped and not line.startswith(' ') and not line.startswith('\t'):
                # This is a line at column 0, check if it should be indented
                if line_num > 1:
                    prev_line = lines[line_num - 2].strip()
                    if prev_line.endswith(':') and not line_stripped.startswith(('def ', 'class ', 'if ', 'elif ', 'else:', 'try:', 'except', 'finally:', 'for ', 'while ', 'with ', '@')):
                        if not line_stripped.startswith('#') and line_stripped:
                            issues_found.append(f"Line {line_num}: Possible indentation error after colon")
            
            # Check for specific syntax patterns
            if 'else:' in line_stripped:
                # Check if else is properly paired
                if line_num < len(lines):
                    next_lines = [lines[i].strip() for i in range(line_num, min(line_num + 3, len(lines)))]
                    # Look for proper indentation after else
                    if len(next_lines) > 1 and next_lines[1] and not next_lines[1].startswith(' '):
                        issues_found.append(f"Line {line_num}: 'else:' may have indentation issues")
            
            # Check for unclosed parentheses, brackets, braces
            open_parens = line.count('(') - line.count(')')
            open_brackets = line.count('[') - line.count(']')
            open_braces = line.count('{') - line.count('}')
            
            if open_parens > 0 or open_brackets > 0 or open_braces > 0:
                # This line has unclosed delimiters - check if properly continued
                if not line.rstrip().endswith('\\') and line_num < len(lines):
                    next_line = lines[line_num].strip()
                    if not next_line or (next_line and not any(next_line.startswith(x) for x in [' ', '\t'])):
                        issues_found.append(f"Line {line_num}: Possible unclosed delimiters")
        
        # Print all found issues
        if issues_found:
            print("\n❌ POTENTIAL SYNTAX ISSUES FOUND:")
            for issue in issues_found:
                print(f"   {issue}")
        else:
            print("\n✅ No obvious line-level syntax issues detected")
        
        # Focus on the known problematic area around line 327
        print(f"\n🎯 FOCUS ON LINE 327 AREA:")
        problem_start = max(1, 327 - 5)
        problem_end = min(len(lines), 327 + 5)
        
        for i in range(problem_start - 1, problem_end):
            marker = ">>> " if i + 1 == 327 else "    "
            print(f"{marker}{i+1:3d}: {lines[i].rstrip()}")
        
        # Analyze the indentation structure around line 327
        print(f"\n🔍 INDENTATION ANALYSIS AROUND LINE 327:")
        for i in range(problem_start - 1, problem_end):
            line = lines[i]
            leading_spaces = len(line) - len(line.lstrip())
            marker = ">>> " if i + 1 == 327 else "    "
            print(f"{marker}{i+1:3d}: [{leading_spaces:2d} spaces] {line.rstrip()}")
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    check_web_dashboard_syntax()
