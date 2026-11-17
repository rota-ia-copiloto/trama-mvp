"""Translate preview runner options to Streamlit; not used by normal installation."""
import sys, subprocess
args=sys.argv[1:]
def opt(name,default):
    try:return args[args.index(name)+1]
    except (ValueError,IndexError):return default
raise SystemExit(subprocess.call([sys.executable,'-m','streamlit','run','app.py','--server.address',opt('--host','127.0.0.1'),'--server.port',opt('--port','3000'),'--server.headless','true']))
