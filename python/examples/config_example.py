#!/usr/bin/python
import makerbotapi
import sys

if __name__ == '__main__':
    config = makerbotapi.makerbotapi.Config()
    config.load()
    
    config.save()
    
    