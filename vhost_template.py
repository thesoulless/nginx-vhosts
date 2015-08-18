#!/usr/bin/env python

__status__ = "Development"

TEMPLATE_WEBSITE = """
#GENERATED by nginx-vhosts

server {
    %(ports)s
    %(server_name)s

    access_log /var/log/nginx/%(slug)s.access.log;
    error_log /var/log/nginx/%(slug)s.error.log;

    root %(root)s;
    index index.html index.htm index.php;

    fastcgi_split_path_info ^(.+\.php)(/.+)$;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    %(custom_conf)s

    %(locations)s
}

"""

TEMPLATE_LOCATION = """
    location %(match)s %(pattern)s {
        %(path)s
        %(custom_conf)s
        %(content)s
    }
"""

TEMPLATE_LOCATION_CONTENT_PHP_FCGI = """
        fastcgi_index index.php;
        #include fcgi.conf;
        fastcgi_pass unix:/var/run/php-fpm/%(id)s.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
"""