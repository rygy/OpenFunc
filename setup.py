from setuptools import setup

setup(name='osfunc',
      version='0.0.1',
      description='Functional Testing for OpenStack',
      author='Hewlett-Packard Operational Monitoring',
      author_email='hppc.operational.monitoring@hp.com',
      packages=['osfunc'],
      entry_points={
          'console_scripts': ['osfunc = osfunc.shell:main']
      })