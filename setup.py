import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ansible-deployment", # Replace with your own username
    version="0.1",
    author="Michael Wilson",
    author_email="mw@1wilson.org",
    description="CLI application to manage ansible deployments.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/torarg/ansible-deployment",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities"
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['ansible_deployment=ansible_deployment.cli:cli']
    },
    install_requires=['jinja2', 'PyYAML']
)