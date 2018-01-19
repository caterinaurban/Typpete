try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Typpete',
    'author': 'Caterina Urban',
    'url': 'https://github.com/caterinaurban/Typpete',
    'download_url': 'https://github.com/caterinaurban/Typpete',
    'author_email': 'caterina.urban@gmail.com',
    'version': '0.1',
    'install_requires': [
        'astunparse',
        'z3'
    ],
    'packages': find_packages(),
    'scripts': [],
    'name': 'Typpete',
    'entry_points': {
        'console_scripts': ['typpete=typpete.tests.inference_runner:run_inference'],
    }
}

setup(**config)
