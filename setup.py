from setuptools import setup

setup(
    name='Trading Calculator',
    version='1.0',
    packages=[],
    install_requires=[
        'websockets==8.*',
        'marshmallow==3.11.*',
        # test dependencies
        'parameterized==0.8.*',
    ]
)
