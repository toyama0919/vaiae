# vaiae

[![PyPI version](https://badge.fury.io/py/vaiae.svg)](https://badge.fury.io/py/vaiae)
[![Build Status](https://github.com/toyama0919/vaiae/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/toyama0919/vaiae/actions/workflows/ci.yml)


Command Line utility for Amazon Aurora.

Supports python 3.8 and above.

## Settings

```sh
export AWS_ACCESS_KEY_ID=XXXXXXXXXXXXXXXXXXXX
export AWS_SECRET_ACCESS_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
export AWS_DEFAULT_REGION=xx-xxxxxxx-x
```

* support environment variables and iam role.

## Examples

#### list instance and cluster

```bash
$ vaiae list

[instances]
db01 mysql available db.m3.xlarge  ap-northeast-1c None
db02 mysql available db.m3.xlarge  ap-northeast-1c None
db03 mysql available db.m3.large ap-northeast-1c None
db04 mysql available db.m3.large ap-northeast-1c None
db05 aurora available db.t2.medium  ap-northeast-1c aurora-cluster
db06 aurora available db.t2.medium  ap-northeast-1c aurora-cluster

[clusters]
aurora-cluster available aurora  ['db05', 'db06']
...
```

## Installation

```sh
pip install vaiae
```

## CI

### install test package

```
$ ./scripts/ci.sh install
```

### test

```
$ ./scripts/ci.sh run-test
```

flake8 and black and pytest.

### release pypi

```
$ ./scripts/ci.sh release
```

git tag and pypi release.
