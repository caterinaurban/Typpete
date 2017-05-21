try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Lyra',
    'author': 'Caterina Urban',
    'url': 'https://github.com/caterinaurban/Lyra',
    'download_url': 'https://github.com/caterinaurban/Lyra',
    'author_email': 'caterina.urban@gmail.com',
    'version': '0.1',
    'install_requires': [],
    'packages': ['lyra'],
    'scripts': [],
    'name': 'Lyra'
}

setup(**config, install_requires=['z3'])