#!/usr/bin/env python
"""
@file server.py
@author Paul Hubbard
@date 2/4/11
@brief Patchlevel oracle, an http server that returns patchlevel numbers for packages.
@author Roger Unwin
@date 2/8/11
@brief Modified to track historical versions, and have a human interface for their display.


Algorithm: Post-increment, save in config file, with a stanza per package.
"""

from ConfigParser import SafeConfigParser as config
import logging as log
from datetime import datetime

from twisted.web import resource
from twisted.web.server import Site
from twisted.internet import reactor

CONFIG_FILENAME = 'config.ini'
TCP_PORT = 2222

class PLR(resource.Resource):
    """
    Class to represent a package, which is saved as a section in the config file.
    """
    def __init__(self, package_name, git_hash=None):
            resource.Resource.__init__(self)
            self.package_name = package_name
            self.git_hash = git_hash

    def get_info(self, package_name):
        """
        For a package name, return last version and git hash, if any.
        Returns an (int, string, string).
        If a new package, patchlevel is zero.
        """
        try:
            c = config()
            c.read(CONFIG_FILENAME)
            patchlevel = c.getint(package_name, 'patchlevel')
            log.debug('Read %d for %s' % (patchlevel, package_name))
        except:
            log.exception('Error getting info')
            patchlevel = 0

        try:
            git_hash = c.get(package_name, 'git_hash')
        except:
            git_hash = ''

        try:
            tstamp_str = c.get(package_name, 'last_update')
        except:
            tstamp_str = None

        return patchlevel, git_hash, tstamp_str

    def write_info(self, package_name, patchlevel, git_hash='None'):
        try:
            c = config()
            c.read(CONFIG_FILENAME)
            # New package?
            if not c.has_section(package_name):
                c.add_section(package_name)

            for x in range(1000, 0, -1):
                if c.has_option(package_name, 'last' + str(x)):
                    c.set(package_name, 'last' + str(x +1), c.get(package_name, 'last' + str(x)))
		
            # last-update timestamp
            self.tstamp = str(datetime.now())

            c.set(package_name, 'last1', str(patchlevel) + ',' + str(git_hash) + ',' + str(self.tstamp))
            c.set(package_name, 'patchlevel', str(patchlevel))
            c.set(package_name, 'git_hash', str(git_hash))
            c.set(package_name, 'last_update', self.tstamp)

            with open(CONFIG_FILENAME, 'w') as configfile:
                c.write(configfile)

            log.info('Wrote %s %d %s %s' % (package_name, patchlevel, git_hash, self.tstamp))
        except:
            log.exception('Error writing config file!')

    def render_GET(self, request):
        if self.package_name == 'favicon.ico':
            log.debug('Ignoring favicon request')
            return ''

        # We don't need a root page, but it is much more friendly with one.
        if self.package_name == '':
            log.debug('Root page requested')
            header = '<html><head><title>Patchlevel Oracle</title></head><body><h3>Packages</h3>'
            body_prefix = '<p><p>'
            table_header = '<table border="1"><tr><th>Package</th><th>Download</th><th>Git commit hash</th><th>Last update</th></tr>'
            table_footer = '</table>'
            footer = '</nl></body></html>'

            request.write(header)
            request.write(body_prefix)
            request.write(table_header)

            # Try to load and read the config file, each section is a package name
            c = config()
            try:
                c.read(CONFIG_FILENAME)
                sections = c.sections()
                for cur_package in sections:
                    pl, ghash, tstamp = self.get_info(cur_package)
                    request.write('<tr><td><a href="%s">%s</td><td><a href="http://ooici.net/releases/%s.tar.gz">%s</a></td><td> <A HREF="https://github.com/ooici/ion-object-definitions/commit/%s">%s</a></td><td>%s</td></tr>' %
                                  (cur_package, cur_package, cur_package + '-pl' + str(pl), cur_package + '-pl' + str(pl),ghash, ghash, tstamp))
            except:
                pass

            request.write(table_footer)
            request.write(footer)

            return ''


        # if a git_hash is present, then we bump the count, and return the count.
        if self.git_hash != None:    
          # We actually return the entry from the file
          patchlevel, git_hash, timestamp = self.get_info(self.package_name)
          # Write next entry
          patchlevel += 1
          self.write_info(self.package_name, patchlevel, self.git_hash)
          return(str(patchlevel))


        """
        This is actually the normal case, have requested a package via REST URL
         e.g. 'GET /nimboss?git_hash=7abcdefg'
        git_hash is optional
        """
        # read previous entry
        try:
            c = config()
            c.read(CONFIG_FILENAME)
            patchlevel = c.getint(self.package_name, 'patchlevel')
        except:
            log.exception('Error getting info')
            patchlevel = 0

        patchlevel, git_hash, timestamp = self.get_info(self.package_name)
        # Write next entry
        # We actually return the entry from the file

        try:
            git_hash = c.get(self.package_name, 'git_hash')
        except:
            git_hash = ''

        try:
            tstamp_str = c.get(self.package_name, 'last_update')
        except:
            tstamp_str = None



        header = '<html><head><title>Patchlevel Oracle</title></head><body><h3>Packages</h3>'
        body_prefix = '<p>Recent version history for ' + self.package_name + '<p>'
        table_header = '<table border="1"><tr><th>Info</th><th>Download</th><th>Git commit hash</th><th>Last update</th></tr>'
        table_footer = '</table>'
        footer = '</nl></body></html>'
        request.write(header)
        request.write(body_prefix)
        request.write(table_header)
        request.write('<tr><td>%s</td><td><a href="http://ooici.net/releases/%s.tar.gz">%s</a></td><td><a href="https://github.com/ooici/ion-object-definitions/commit/%s">%s</a></td><td>%s</td></tr>' %
                      ('Current', self.package_name + '-pl' + str(patchlevel), self.package_name + '-pl' + str(patchlevel), git_hash, git_hash, tstamp_str))

        for x in range(2,1000):
            try:
                s = c.get(self.package_name, 'last' + str(x))
                items = s.split(',')
                request.write('<tr><td>%s</td><td><a href="http://ooici.net/releases/%s.tar.gz">%s</a></td><td><a href="https://github.com/ooici/ion-object-definitions/commit/%s">%s</a></td><td>%s</td></tr>' %
                              ('Historical',  self.package_name + '-pl' + items[0], self.package_name + '-pl' + items[0], items[1], items[1], items[2]))
            except:
                """
                """

        request.write(table_footer)
        request.write(footer)

        return ''
        

class PLRootPage(resource.Resource):
    """
    If a child is requested, generate it on the fly (will create a new package record)
    Also pass in git_hash if it's in the HTTP request.
    """
    def getChild(self, package_name, request):
        try:
            ghash = request.args.get('git_hash')[0]
            self.ghash = ghash
            log.debug(ghash)
        except:
            log.debug('No git_hash in arguments')
            ghash = None
            self.ghash = None

        log.debug('"%s"' % package_name)
        return PLR(package_name, git_hash=ghash)

def main():
    log.basicConfig(level=log.INFO,
        format='%(asctime)s %(levelname)s [%(funcName)s] %(message)s')

    root = PLRootPage()
    factory = Site(root)
    reactor.listenTCP(TCP_PORT, factory)
    log.info('http://localhost:%d/' % TCP_PORT)

if __name__ == '__main__':
    main()
    reactor.run()
