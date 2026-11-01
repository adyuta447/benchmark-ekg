import platform, subprocess, sys, importlib.metadata as md, psutil

def info(libs=()):
    cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip() or platform.processor()
    d = {"cpu": cpu, "inti_fisik": psutil.cpu_count(False), "inti_logis": psutil.cpu_count(True),
         "ram_gb": round(psutil.virtual_memory().total / 2**30, 1), "os": platform.platform(),
         "python": sys.version.split()[0]}
    for l in libs:
        try: d[l] = md.version(l)
        except md.PackageNotFoundError: d[l] = "tidak terpasang"
    return d
