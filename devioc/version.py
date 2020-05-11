# Based on: https://github.com/Changaco/version.py

import os
import re
from subprocess import CalledProcessError, check_output

NAME = 'devioc'
PREFIX = 'v'

tag_re = re.compile(rf'\btag: {PREFIX}([0-9][^,]*)\b')
version_re = re.compile('^Version: (.+)$', re.M)


def get_version():
    # Return the version if it has been injected into the file by git-archive
    version = tag_re.search('$Format:%D$')
    if version:
        return version.group(1)

    package_dir = os.path.dirname(os.path.dirname(__file__))

    if os.path.isdir(os.path.join(package_dir, '.git')):
        # Get the version using "git describe".
        version_cmd = 'git describe --tags --abbrev=0'
        release_cmd = 'git rev-list HEAD ^$(git describe --abbrev=0) | wc -l'
        try:
            version = check_output(version_cmd, shell=True).decode().strip()
            release = check_output(release_cmd, shell=True).decode().strip()
            return f'{version}.{release}'.strip(PREFIX)
        except CalledProcessError:
            raise RuntimeError('Unable to get version number from git tags')
    else:
        try:
            from importlib import metadata
        except ImportError:
            # Running on pre-3.8 Python; use importlib-metadata package
            import importlib_metadata as metadata

        version = metadata.version(NAME)

    return version