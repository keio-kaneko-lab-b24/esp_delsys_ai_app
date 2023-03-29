import subprocess

subprocess.call(
    f"pio run --target upload", shell=True)
