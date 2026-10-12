FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# The image includes a Yarn package source whose signing key is no longer
# valid, which makes every apt-get update fail. The lab does not use Yarn.
RUN rm -f /etc/apt/sources.list.d/yarn.list
