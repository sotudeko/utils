#!/bin/bash

python3 import_baseurl_mail_proxy.py
python3 import_orgs_apps.py
# make sure all users are in the target instance
python3 import_roles.py
python3 import_rolemappings.py