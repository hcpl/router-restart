#! /usr/bin/env python3

import requests
from requests import Timeout, ConnectionError, HTTPError

from argparse import ArgumentParser, RawTextHelpFormatter
import logging
import os
import sys
import json


# List of supported devices
SUPPORTED_DEVICES = {
    'TP-Link': ['TL-WR841N',
                'TL-WR941N',
                '... maybe all other TP-Link`s?']
}

# Default settings
DEFAULTS = {
    'HOST': '192.168.0.1',
    'PORT': 80,
    'USERNAME': 'admin',
    'PASSWORD': 'admin'
}


# Command line related string variables
description = ('Authorizes as the administrator on your router\n'
               'and attempts to restart it.\n'
               'Currently supported devices are:\n'
               + '\n'.join('  * %s\n' % brand +
                           '\n'.join('    - %s' % model for model in models)
                           for (brand, models) in SUPPORTED_DEVICES.items()))
host_help = 'specify the host IP or the host name'
port_help = 'specify the port'
username_help = 'specify the username'
password_help = 'specify the password'
config_file_help = ('options defined in this file are taken\n'
                    'if not specified explicitly by command-line options')
reboot_help = ('if specified, reboot will happen\n'
               'instead of reconnection')
simulate_help = 'no action; simulate events only'
dry_run_help = 'same as --simulate'
v_help = ("sets the verbosity level equal to\n"
          "the number of 'v' letters")
verbose_help = ('set the verbosity level equal to\n'
                'the VERBOSITY parameter')

values_resolution_epilog = ('Host, port, username and password values '
                            'are resolved in this order:\n'
                            '  1. Command-line options\n'
                            '  2. CONF_FILE settings\n'
                            '  3. ~/.router-restart.conf settings\n'
                            '  4. Default internal values')
defaults_epilog = ('Default settings internally set by this program are:' +
                   ''.join('\n  --%s %s' % (k.lower(), v)
                           for (k, v) in DEFAULTS.items()))
epilog = values_resolution_epilog + '\n\n' + defaults_epilog


# Creates the arguments parser
def create_args_parser():
    parser = ArgumentParser(description=description,
                            epilog=epilog,
                            formatter_class=RawTextHelpFormatter)

    parser.add_argument("-o", "--host",
                        help=host_help)
    parser.add_argument("-p", "--port", type=int,
                        help=port_help)
    parser.add_argument("-u", "--username", metavar='NAME',
                        help=username_help)
    parser.add_argument("-w", "--password", metavar='PASS',
                        help=password_help)
    parser.add_argument("-c", "--config-file", metavar='CONF_FILE',
                        help=config_file_help)
    parser.add_argument("-r", "--reboot",
                        action='store_true', help=reboot_help)
    parser.add_argument("-s", "--simulate", dest='dry_run',
                        action='store_true', help=simulate_help)
    parser.add_argument("--dry-run", dest='dry_run',
                        action='store_true', help=dry_run_help)

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", dest='verbosity',
                       default=0, action='count', help=v_help)
    group.add_argument("--verbose", dest='verbosity',
                       default=0, type=int, help=verbose_help)

    return parser

# Configures logger by a passed verbosity value
def configure_logger(verbosity):
    global logger

    format = ('%(message)s'
                  if verbosity in (0, 1) else
              '[%(asctime)s %(levelname)s] %(message)s'
                  if verbosity in (2, 3) else
              '[%(asctime)s %(levelname)s %(name)s] %(message)s')
    datefmt = '%H:%M:%S'
    level = (logging.WARNING if verbosity == 0 else
             logging.INFO if verbosity in (1, 2) else
             logging.DEBUG)

    logging.basicConfig(format=format, datefmt=datefmt, level=level)
    logger_name = os.path.basename(sys.argv[0])
    logger = logging.getLogger(logger_name)

def apply_configs(args, config_file):
    def set_from_dict(d, key_func=None):
        if key_func == None:
            key_func = lambda x: x

        for k in args.__dict__:
            if getattr(args, k) == None and key_func(k) in d:
                setattr(args, k, d[key_func(k)])

    if config_file != None:
        with open(config_file) as f:
            d = json.load(f)
            set_from_dict(d)

    if os.path.isfile('~/.router-restart.conf'):
        with open('~/.router-restart.conf') as f:
            d = json.load(f)
            set_from_dict(d)

    set_from_dict(DEFAULTS, key_func=str.upper)

# Actual working is done here
# This function makes a single request
def make_request(host, port, username, password, option_key, dry_run):
    if option_key in ('Connect', 'Disconnect'):
        menu_name = 'Status'
        option = option_key + '=any_string&wan=1'
    elif option_key == 'Reboot':
        menu_name = 'SysReboot'
        option = 'Reboot=any_string'
    else:
        raise ValueError('invalid option key: %s' % option_key)

    url = ('http://%s:%s/userRpm/%sRpm.htm?%s' %
           (host, port, menu_name, option))

    logger.debug('Host: %s' % host)
    logger.debug('Port: %s' % port)
    logger.debug('URL: %s' % url)
    logger.debug('Username: %s' % username)
    logger.debug('Password: %s' % password)

    try:
        logger.info('Trying to connect to the router...')

        if dry_run:
            resp = requests.Response()
            resp.status_code = 200
        else:
            resp = requests.get(url, auth=(username, password),
                                timeout=(3.10, 5))
    except Timeout as err:
        logger.error('Timeout connecting to the router or '
                     'waiting for data from the router')
        logger.error(str(err) + '\n')
    except ConnectionError as err:
        logger.error('Unable to connect to the router: '
                     'either wrong hostname or wrong port')
        logger.error(str(err) + '\n')
    else:
        logger.info('Connected successfully!')

        # Response interpretation

        try:
            resp.raise_for_status()
        except HTTPError as err:
            logger.error('Restart failed, please try again')
            logger.error(str(err) + '\n')
        else:
            if option_key == 'Connect':
                logger.info('Gaining Internet access. Wait some seconds...\n')
            elif option_key == 'Disconnect':
                logger.info('Disconnected from Internet...\n')
            elif option_key == 'Reboot':
                logger.info('Reboot is in progress now. Wait a minute...\n')

# Routes to make_request() function based on whether
# we are rebooting device or not
def process_action(host, port, username, password, reboot, dry_run):
    if reboot:
        make_request(host, port, username, password, 'Reboot', dry_run)
    else:
        make_request(host, port, username, password, 'Disconnect', dry_run)
        make_request(host, port, username, password, 'Connect', dry_run)


# The main function
def main():
    parser = create_args_parser()
    args = parser.parse_args()

    configure_logger(args.verbosity)
    apply_configs(args, args.config_file)

    process_action(args.host, args.port, args.username,
                   args.password, args.reboot, args.dry_run)

if __name__ == '__main__':
    main()
