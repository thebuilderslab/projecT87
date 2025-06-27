
import py_compile
try:
    py_compile.compile('arbitrum_testnet_agent.py', doraise=True)
    print('✅ arbitrum_testnet_agent.py: Syntax OK')
except py_compile.PyCompileError as e:
    print(f'❌ arbitrum_testnet_agent.py: {e}')
try:
    py_compile.compile('web_dashboard.py', doraise=True)
    print('✅ web_dashboard.py: Syntax OK')
except py_compile.PyCompileError as e:
    print(f'❌ web_dashboard.py: {e}')
