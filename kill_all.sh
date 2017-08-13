#!/usr/bin/env bash
docker kill dispatcher
docker kill master
docker kill replica
docker rm dispatcher
docker rm master
docker rm replica
