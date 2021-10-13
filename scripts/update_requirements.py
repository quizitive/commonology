#!/usr/bin/env python
import sys
import subprocess

# This script will install all the packages in requirement.txt without pegging versions.
# Then it will list new versions installed for an updated requirements.txt file.

# How to remove all packages? `pip uninstall -y -r <(pip freeze)`


with open('requirements.txt', 'r') as fh:
    lines = fh.readlines()

git_packages = [i.strip() for i in lines if 'git+http' in i]

required_packages = [i.split('=')[0].strip() for i in lines if i.strip()]

subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])

for package_name in required_packages:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])

reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
installed_packages = [r.decode() for r in reqs.split()]

new_required_packages = {i.split('=')[0].strip(): i for i in installed_packages}
for i in required_packages:
    if i in git_packages:
        print(i)
    else:
        try:
            print(new_required_packages[i])
        except KeyError:
            print('KeyError', i)
