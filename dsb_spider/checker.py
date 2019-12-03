from pip._internal.utils.misc import get_installed_version
import os
import subprocess


def get_not_installed_packages():
    requirements_txt = "requirements.txt"
    
    if not os.path.exists(requirements_txt):
        return []
    
    need_installed_packages = []
    with open(requirements_txt) as f:
        for line in f.readlines():
            line = line.strip()
            if line == "":
                continue
            
            installed = False
            try:
                installed = bool(get_installed_version(line))
            
            except Exception as ex:
                if hasattr(ex, "__module__") and "pip." in ex.__module__:
                    installed = False
                else:
                    raise
            if not installed:
                need_installed_packages.append(line)
    
    return need_installed_packages

def install(package):
    paths = os.environ.get("PATH").split(":")
    for other_path in ["/usr/local/bin", "/usr/local/sbin", "/usr/bin", "/usr/sbin"]:
        if other_path not in paths:
            paths.append(other_path)

    commands = ["pip3", "pip3.7", "pip"]
    command = None
    for _command in commands:
        command_paths = [ os.path.join(_path, _command) for _path in paths]
        if any([ os.path.isfile(_path) for _path in command_paths]):
            command = _command
            break

    assert command

    p = subprocess.Popen([command, "install", package], env = {
        "PATH": ":".join(paths),
        })

    p.wait()
    
def pip_check():
    for package in get_not_installed_packages():
        install(package)