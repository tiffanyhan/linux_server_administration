Information for Review of
'Linux Server Configuration' Project
=====================================

IP address: 52.43.165.7
SSH port: 2200
Private SSH key: to be included in 'notes to reviewer' section
Password for user 'grader': to be included in 'notes to reviewer' section
Public URL: http://ec2-52-43-165-7.us-west-2.compute.amazonaws.com/

Configuration changes made:
  - created a new user named 'grader'
  - gave 'grader' access to the sudo command
  - 'grader' must enter their password at least once to use sudo
  - 'grader' must use key-based authentication to login
  - disabled remote login of the root user

  - moved ssh from default port 22 to port 2200
  - enabled a firewall that only allows connections for ssh, http, and ntp

  - ensured all applications are up-to-date
  - configured the local timezone to UTC

  - installed and configured apache2 to serve a python mod_wsgi app

  - installed postgresql
  - postgresql by default does not allow remote connections
  - created a new postgresql user named catalog
  - only 'catalog' can access the catalog database used by the app
  - 'catalog' has limited permissions (revoked TRUNCATE and TRIGGER privileges on all tables in the db)

  - installed git

Software installed:
  - apache2
  - postgresql
  - psycopg2
  - sqlalchemy
  - flask
  - oauth2client.client
  - mod_wsgi
  - virtualenv

Resources used:
  - https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps
  - http://docs.sqlalchemy.org/en/latest/core/engines.html
  - http://www.ducea.com/2006/06/18/linux-tips-password-usage-in-sudo-passwd-nopasswd/
  - postgresql official documentation
  - stackoverflow.com
