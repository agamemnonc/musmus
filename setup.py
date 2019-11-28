# License: MIT

from os.path import realpath, dirname, join
from setuptools import setup, find_packages
import musmus

VERSION = musmus.__version__
PROJECT_ROOT = dirname(realpath(__file__))

REQUIREMENTS_FILE = join(PROJECT_ROOT, 'requirements.txt')

with open(REQUIREMENTS_FILE) as f:
    install_reqs = f.read().splitlines()

install_reqs.append('setuptools')

setup(name = "musmus",
      version=VERSION,
      description = "Muscle-controlled music.",
      author = "Agamemnon Krasoulis",
      author_email = "agamemnon.krasoulis@gmail.com",
      url = "https://github.com/agamemnonc/musmus",
      packages=find_packages(),
      package_data={'': ['LICENSE.txt',
                         'README.md',
                         'requirements.txt']
                    },
      include_package_data=True,
      install_requires=install_reqs,
      license='MIT',
      platforms='any',
      long_description="""
A thin mido wrapper for controlling audiomulch with MIDI messages.
""")
