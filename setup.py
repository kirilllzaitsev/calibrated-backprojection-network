# Example 1: simple setup.py file for a pacakge called packagename

# Import "setup" method from setuptools
import os
from setuptools import setup
import shutil
# setup is the gateway to the package build process.
# The only required components for a package are
# the name, author and contact, and description.
setup(
    name='kbnet',
    version='0.1.0',
    author='Alex Wong',
    author_email='alexw@cs.ucla.edu',
    description='Calibrated Backprojection Network (KBNet)',
    license='Academic Software License',
    url='https://github.com/alexklwong/calibrated-backprojection-network',
    packages=['kbnet'],
    zip_safe=False
)