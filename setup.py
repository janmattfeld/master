from distutils.core import setup

setup(
    name='untitled2',
    version='1.0.0',
    packages=[''],
    url='https://github.com/janmattfeld',
    license='MIT',
    author='Jan-Henrich Mattfeld',
    author_email='dev-cloudstack@janmattfeld.de',
    description='Multi-Cloud Broker', requires=['jinja2', 'apache-libcloud', 'requests', 'tableprint', 'coloredlogs']
)
