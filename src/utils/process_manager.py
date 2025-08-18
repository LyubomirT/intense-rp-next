import psutil, os

def kill_driver_processes() -> None:
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name']
            base_name = os.path.splitext(proc_name)[0]
            
            if base_name in ["chromedriver", "geckodriver", "msedgedriver", "uc_driver"]:
                print(f"Terminating process: {proc_name} (PID: {proc.info['pid']})")
                proc.terminate()
        
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def kill_tunnel_processes() -> None:
    """Clean up cloudflared tunnel processes"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            proc_name = proc.info['name']
            cmdline = proc.info.get('cmdline', [])
            
            # Look for cloudflared processes by name
            if 'cloudflared' in proc_name.lower():
                print(f"Terminating cloudflared process: {proc_name} (PID: {proc.info['pid']})")
                proc.terminate()
            # Also check for processes with cloudflared in command line arguments
            elif cmdline and any('cloudflared' in str(arg) for arg in cmdline):
                print(f"Terminating cloudflared-related process: {proc_name} (PID: {proc.info['pid']})")
                proc.terminate()
        
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

def kill_all_processes() -> None:
    """Clean up both driver and tunnel processes"""
    kill_driver_processes()
    kill_tunnel_processes()