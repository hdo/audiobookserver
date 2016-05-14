import os
import sys
import subprocess
import re

def get_ip():
    proc = subprocess.Popen(['ifconfig'], stdout=subprocess.PIPE, )
    stdout_data = proc.communicate()[0]
    ip_adr = re.findall('inet addr:(.*?)  Bcast:', stdout_data)
    if len(ip_adr) > 0:
    # assume it's the first ip adress
        return ip_adr[0]
    return ""


