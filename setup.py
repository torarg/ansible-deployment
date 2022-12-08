import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ansible-deployment", # Replace with your own username
    version="0.7.1",
    author="Michael Wilson",
    author_email="mw@1wilson.org",
    description="CLI application to manage ansible deployments.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/torarg/ansible-deployment-cli",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities"
    ],
    python_requires='>=3.9',
    entry_points={
        'console_scripts': ['ansible-deployment=ansible_deployment.cli:main']
    },
    install_requires=[
                        'jinja2==2.11.3',
                        'PyYAML==5.4.1',
                        'click==8.0.1',
                        'ansible==4.3.0',
                        'GitPython==3.1.18',
                        'cryptography==3.4.7',
                        'hvac==0.11.0'
                    ],
    include_package_data=True
)
