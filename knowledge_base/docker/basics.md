# Docker Basics

## What Docker Is Used For

Docker packages an application and its runtime dependencies into an image. A
container is a running instance of that image. This makes development setup
more repeatable because the application uses the same operating-system
environment and dependency versions on different machines.

A `Dockerfile` describes how to build one image. Common instructions select a
base image, choose a working directory, copy files, install dependencies, and
define the startup command.

## Docker Compose

Docker Compose describes multiple related services in one YAML file. It can
build and start a frontend and backend together, expose ports, pass environment
variables, and create shared volumes.

Containers have their own network namespace. A browser still uses published
host addresses such as `http://localhost:8000`, while containers can use
Compose service names to communicate with each other.

## Persistent Data

Container files normally disappear when a container is replaced. A Docker
volume stores runtime data independently from the container lifecycle. Volumes
are suitable for generated database files that should survive a restart.

Images should not contain secrets or generated development data. Environment
files, caches, virtual environments, `node_modules`, and build output are
commonly excluded from the build context or Git repository.
