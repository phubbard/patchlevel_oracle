
"""
@file deploy.tac
@author Paul Hubbard
@date 2/4/11
@brief Twisted deployment file for patchlevel oracle.
@see https://github.com/phubbard/patchlevel_oracle
"""
import logging as log

from twisted.web import resource
from twisted.web.server import Site
from twisted.internet import reactor

from twisted.application import service
from twisted.application import internet

# Sloppy but effective
from server import *

log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s [%(funcName)s] %(message)s')
application = service.Application('patchlevel-oracle')

root = PLRootPage()
factory = Site(root)
ws = internet.TCPServer(TCP_PORT, factory)
ws.setServiceParent(service.IServiceCollection(application))
