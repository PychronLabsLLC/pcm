[![Publish Python 🐍 distributions 📦 to PyPI and TestPyPI](https://github.com/PychronLabsLLC/pcm/actions/workflows/publish-to-pypi.yml/badge.svg)](https://github.com/PychronLabsLLC/pcm/actions/workflows/publish-to-pypi.yml)
[![Format code](https://github.com/PychronLabsLLC/pcm/actions/workflows/format_code.yml/badge.svg)](https://github.com/PychronLabsLLC/pcm/actions/workflows/format_code.yml)

# pcm 
Pychron Configuration Manager

This is a simple "command line interface" aka `cli` for build pychron configuration
files. 

It can also be used to install the pychron source code, build the necessary python environment and install launcher 
scripts

# Prerequisites
1. Install [Miniconda](https://docs.anaconda.com/miniconda/miniconda-install/)
2. Install git
   1. for windows download from [git-scm.com](https://git-scm.com/download/win) 
   2. for mac use 
      ```shell
      $ xcode-select --install
      ```


# Installation

```shell
pip install pychron-cm
```

# Usage


```shell

pcm wizard
```
or for help

```shell
pcm --help
```


# Manually build EDM environment
```shell
edm shell -e pychron chaco,certifi,cython,envisage,future,gitpython,keyring,jinja2,lxml,numpy,pandas,patsy,pillow,pip,pyface,pyparsing,pyproj,pyqt5,pytables,pyyaml,pygments,qt,Reportlab,requests,scipy,sqlalchemy,traits,xlrd,xlsxwriter,xlwt,statsmodels
pip install --no-dependencies uncertainties qimage2ndarray pymysql
```
