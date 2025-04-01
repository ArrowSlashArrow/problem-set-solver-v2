# name: A Very Secret Algorithm
# version: 2
# description: Does something very secret...
# tags: secret adder alg3

import subprocess

def solver():
    print("The module may take a while.")
    cmd = 'Get-ChildItem -Path C:\\Users\\anton -Recurse'
    process = subprocess.Popen(['powershell', '-Command', cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    if process.returncode == 0:
        print(stdout)
    else:
        print('yo why tf did you not let me do this:')
        raise Exception(f"Error: {stderr}")