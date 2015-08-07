# MakerBot Gen 5 API

## The goal of this project is to provide a Python API for controlling the MakerBot 5th Generation 3D printers

### Current Features:
 * Oauth authentication (fcgi / jsonrpc) 
 * Get printer status (nozzle temp, print progress, ...)
 * Access the camera
 
### Installing:
 * Clone/download the API
 * Run "python/setup.py" (Tested with Python 2.7)
 
### Common Issues:
 * If you have MakerBot Desktop / MakerWare installed, chances are the conveyor service is running in the background. This service takes hold of the ports used for running discover.py. In MakerBot Desktop, go to Services -> Stop Background Service to be able to discover bots on your network.
 
[![Build Status](https://travis-ci.org/gryphius/makerbot-gen5-api.svg)](https://travis-ci.org/gryphius/makerbot-gen5-api)
