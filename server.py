#!/usr/bin/env python
"""
@file server.py
@author Paul Hubbard
@date 2/4/11
@brief Patchlevel oracle, an http server that returns patchlevel numbers for packages.

Algorithm: Post-increment, save in config file, with a stanza per package.
"""

from ConfigParser import SafeConfigParser as config
import logging as log
from datetime import datetime

from twisted.web import resource
from twisted.web.server import Site
from twisted.internet import reactor

CONFIG_FILENAME = 'config.ini'

class PLR(resource.Resource):
    def __init__(self, package_name, git_hash=None):
            resource.Resource.__init__(self)
            self.package_name = package_name
            self.git_hash = git_hash

    def get_info(self, package_name, want_string=False):
        """
        For a package name, return last version and git hash, if any.
        Returns an (int, string) or string, zero-length if not found.
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


        if want_string:
            return('%d %s %s' % (patchlevel, git_hash, tstamp_str))
        else:
            return patchlevel, git_hash, tstamp_str

    def write_info(self, package_name, patchlevel, git_hash=None):
        try:
            c = config()
            c.read(CONFIG_FILENAME)
            # New package?
            if not c.has_section(package_name):
                c.add_section(package_name)

            c.set(package_name, 'patchlevel', str(patchlevel))
            if git_hash:
                c.set(package_name, 'git_hash', git_hash)

            # last-update timestamp
            tstamp = str(datetime.now())
            c.set(package_name, 'last_update', tstamp)

            with open(CONFIG_FILENAME, 'w') as configfile:
                c.write(configfile)

            log.info('Config file written OK')
        except:
            log.exception('Error writing config file!')

    def render_GET(self, request):
        if self.package_name == 'favicon.ico':
            log.debug('Ignoring favicon request')
            return ''

        if self.package_name == '':
            log.info('Root page requested, enumerating sections')
            header = '<html><head><title>Patchlevel Oracle</title></head><body><h3>Packages listed in "%s"</h3>' % CONFIG_FILENAME
            body_prefix = '<p>Clicking a package returns and increments the version number<p>'
            table_header = '<table border="0"><tr><th>Package</th><th>Patchlevel</th><th>Git commit hash</th><th>Last update</th></tr>'
            table_footer = '</table>'
            footer = '</nl></body></html'

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
                    request.write('<tr><td><a href="%s">%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' %
                                  (cur_package, cur_package, str(pl), ghash, tstamp))
            except:
                pass

            request.write(table_footer)
            request.write(footer)

            return ''

        """
        Normal case, have requested a package via REST URL
         e.g. 'GET /nimboss?git_hash=7abcdefg'
        git_hash is optional
        """
        # read previous entry
        patchlevel, git_hash, timestamp = self.get_info(self.package_name)
        # Write next entry
        self.write_info(self.package_name, patchlevel+1, self.git_hash)
        # We actually return the entry from the file
        return(str(patchlevel))

class PLRootPage(resource.Resource):
    def getChild(self, package_name, request):
        try:
            ghash = request.args.get('git_hash')[0]
            log.debug(ghash)
        except:
            log.debug('No git_hash in arguments')
            ghash = None

        log.debug('"%s"' % package_name)
        return PLR(package_name, git_hash=ghash)

def main():
    log.basicConfig(level=log.INFO,
        format='%(asctime)s %(levelname)s [%(funcName)s] %(message)s')

    root = PLRootPage()
    factory = Site(root)
    reactor.listenTCP(2210, factory)
    log.info('http://localhost:2210/')

if __name__ == '__main__':
    main()
    reactor.run()