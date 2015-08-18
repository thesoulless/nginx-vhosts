#!/usr/bin/env python

import subprocess
import argparse

from vhost_template import *

__status__ = "Development"

class Nginx:
    def __init__(self):
        self.vhost_root = '/etc/nginx/sites-available/'
        self.vhost_root_enabled = '/etc/nginx/sites-enabled/'

    def __generate_website_location(self, ws, location):
        params = location.backend.params

        if location.backend.type == 'static':
            content = TEMPLATE_LOCATION_CONTENT_STATIC % {
                'autoindex': 'autoindex on;' if params['autoindex'] else '',
            }

        if location.backend.type == 'proxy':
            content = TEMPLATE_LOCATION_CONTENT_PROXY % {
                'url': params.get('url', 'http://127.0.0.1/'),
            }

        if location.backend.type == 'fcgi':
            content = TEMPLATE_LOCATION_CONTENT_FCGI % {
                'url': params.get('url', '127.0.0.1:9000'),
            }

        if location.backend.type == 'php-fcgi':
            content = TEMPLATE_LOCATION_CONTENT_PHP_FCGI % {
                'id': location.backend.id,
            }

        if location.backend.type == 'python-wsgi':
            content = TEMPLATE_LOCATION_CONTENT_PYTHON_WSGI % {
                'id': location.backend.id,
            }

        if location.backend.type == 'ruby-unicorn':
            content = TEMPLATE_LOCATION_CONTENT_RUBY_UNICORN % {
                'id': location.backend.id,
            }

        if location.backend.type == 'ruby-puma':
            content = TEMPLATE_LOCATION_CONTENT_RUBY_PUMA % {
                'id': location.backend.id,
            }

        if location.backend.type == 'nodejs':
            content = TEMPLATE_LOCATION_CONTENT_NODEJS % {
                'port': location.backend.params.get('port', 8000) or 8000,
            }

        if location.custom_conf_override:
            content = ''

        path_spec = ''
        if location.path:
            if location.path_append_pattern:
                path_spec = 'root %s;' % location.path
            else:
                path_spec = 'alias %s;' % location.path

        return TEMPLATE_LOCATION % {
            'pattern': location.pattern,
            'custom_conf': location.custom_conf,
            'path': path_spec,
            'match': {
                'exact': '',
                'regex': '~',
                'force-regex': '^~',
            }[location.match],
            'content': content,
        }

    def generate(self, website):
        params = {
            'slug': website.slug,
            'server_name': (
                'server_name %s;' % (' '.join(domain.domain for domain in website.domains))
            ) if website.domains else '',
            'ports': (
                '\n'.join(
                    'listen %s:%s%s;' % (
                        x.host, x.port,
                        ' default_server' if x.default else '',
                    )
                    for x in website.ports
                )
            ),
            'root': website.root,
            'custom_conf': website.custom_conf,
            'custom_conf_toplevel': website.custom_conf_toplevel,
            'locations': (
                '\n'.join(self.__generate_website_location(website, location) for location in website.locations)
            ) if not website.maintenance_mode else '',
        }
        return TEMPLATE_WEBSITE % params

    def save_configuration(self, content, site_slug):
        with open(self.vhost_root + site_slug, "w") as text_file:
            text_file.write(content)

        subprocess.call([
            'ln', self.vhost_root + site_slug, '-s', self.vhost_root_enabled + site_slug,
        ])

        subprocess.call([
            'service', "nginx", '', "restart",
        ])

class DummyObject: pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--serverip", help="Server ip")
    parser.add_argument("-s", "--slug", help="Website slug")
    parser.add_argument("--domain", help="Website domain")
    parser.add_argument("-r", "--root", help="Website root path")
    args = parser.parse_args()

    website = DummyObject()
    website.slug = args.slug

    port = DummyObject()
    port.host = args.serverip
    port.port = 80
    port.default = False
    website.ports = [port]

    domain = DummyObject()
    domain.domain = args.domain
    website.domains = [domain]

    website.root = args.root

    location = DummyObject()
    backend = DummyObject()
    location.backend = backend
    location.backend.type = "php-fcgi"
    location.backend.id = args.slug
    params = DummyObject()
    params.t = "s"
    location.backend.params = params
    location.custom_conf_override = ""
    location.path = ""
    location.path_append_pattern = ""
    location.pattern = "\.php$"
    location.custom_conf = ""
    location.match = "regex"

    website.locations = [location]

    website.maintenance_mode = False

    website.custom_conf_toplevel = ""
    website.custom_conf = ""

    nginx = Nginx()
    config = nginx.generate(website)
    nginx.save_configuration(config, args.slug)
    print "Done!"
