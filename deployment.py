#!/usr/bin/env python3
#  -*- coding: UTF-8 -*-

import ruamel.yaml as yaml

from cloud import Cloud, AmazonCloud, OpenStackCloud
from log import traced, init

init('DEBUG')

_clouds = []
_apps = []


@traced()
def _get_cloud_config(path='clouds.yaml'):
    """Load Cloud Configurations from File"""
    with open(path) as stream:
        return yaml.YAML().load(stream)


@traced()
def _init_clouds(filter='all'):
    """Create Clouds from Config"""
    for cfg in _get_cloud_config('clouds.yaml'):
        _clouds.append(Cloud(cfg))


@traced()
def _get_service_definition(path='./services/hyrise.yaml'):
    """Load Service Definitions from File"""
    with open(path) as stream:
        return yaml.YAML().load(stream)


# http://libcloud.readthedocs.io/en/latest/container/drivers/docker.html
# Always checking for latest image version
# Port Configuration is undocumented in libcloud
# auto remove (--rm) is unsupported, keep track of containers and remove manually

import app


@traced()
def deploy_app(id='hyrise'):
    """Deploy App"""
    # Get the app definition including a general description and architecture
    template = _get_service_definition('./services/{}.yaml'.format(id))
    sla = {}
    _apps.append(app.App(template, sla, _clouds[0]))


def destroy_app(id='hyrise'):
    """Remove all Instances of an Application"""
    # TODO: Find all instances of specific app


def get_inventory():
    """Get Instances in all Clouds"""
    pass


def get_throughput():
    from query_hyrise import benchmark
    dispatcher_ip = '127.0.0.1'
    dispatcher_port = 5099
    return benchmark(dispatcher_ip, dispatcher_port, './queries/q1.json', num_threads=2, num_queries=4)


_init_clouds()
deploy_app('hyrise')
get_throughput()
# destroy_app('hyrise')
_clouds[0]._destroy_all_containers()
