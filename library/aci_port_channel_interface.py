#!/usr/bin/python

DOCUMENTATION = '''
---

module: aci_port_channel_interface
short_description: Direct access to the APIC API
description:
    - Offers direct access to the APIC API
author: Cisco
requirements:
    - ACI Fabric 1.0(3f)+
notes:
options:
   action:
        description:
            - post, get, or delete
        required: true
        default: null
        choices: ['post','get', 'delete']
        aliases: []
   port_channel:
        description:
            - Port Channel name
        required: true
        default: null
        choices: []
        aliases: []
    max_link:
        description:
            - Maximum Links (range 1-16)
        required: false
        default: '16'
        choices: []
        aliases: []
    min_link:
        description:
            - Minimum Links (range 1-16)
        required: false
        default: '1'
        choices: []
        aliases: []
    mode:
	description: 
	    - Port channel interface policy mode
        required: false
        default: 'off'
        choices: ['off','mac-pin','active','passive','mac-pin-nicload']
        aliases: []
    descr:
        description:
            - Description for Port Channel Interfaces
        required: false
        default: null
        choices: []
        aliases: []
    host:
        description:
            - IP Address or hostname of APIC resolvable by Ansible control host
        required: true
        default: null
        choices: []
        aliases: []
    username:
        description:
            - Username used to login to the switch
        required: true
        default: 'admin'
        choices: []
        aliases: []
    password:
        description:
            - Password used to login to the switch
        required: true
        default: null
        choices: []
        aliases: []
    protocol:
        description:
            - Dictates connection protocol to use
        required: false
        default: https
        choices: ['http', 'https']
        aliases: []
'''

EXAMPLES =  '''

    aci_port_channel_interface:
        action: "{{ action }}"
        port_channel: "{{ port_channel }}"
        max_link: "{{ max_link }}"
        min_link: "{{ min_link }}"
        mode: "{{ mode }}"
        descr: "{{ descr }}"
        host: "{{ inventory_hostname }}"
        username: "{{ username }}"
        password: "{{ password }}"
	protocol: "{{ protocol }}"

'''

import socket
import json
import requests


def main():
    
    ''' Ansible module to take all the parameter values from the playbook '''

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(choices=['get', 'post', 'delete']),
            port_channel=dict(type='str'),
            max_link=dict(type='int', default='16'),
            min_link=dict(type='int', default='1'),
            mode=dict(choices=['off','mac-pin', 'active','passive','mac-pin-nicload'], default='off'),
            descr=dict(type='str',required=False),       
            host=dict(required=True),
            username=dict(type='str', default='admin'),
            password=dict(type='str'),
            protocol=dict(choices=['http', 'https'], default='https'),
        ), 
        supports_check_mode=False
    )

    host = socket.gethostbyname(module.params['host'])
    username = module.params['username']
    password = module.params['password']
    protocol = module.params['protocol']
    action = module.params['action']

    max_link = module.params['max_link']
    max_link = str(max_link)
    min_link = module.params['min_link']
    min_link = str(min_link)
    mode = module.params['mode']
    port_channel = module.params['port_channel']
    descr = module.params['descr']
    descr=str(descr)

    post_uri = '/api/mo/uni/infra/lacplagp-'  + port_channel + '.json'
    get_uri = '/api/node/class/lacpLagPol.json'

    config_data = {
     "lacpLagPol": {
	"attributes": {
	     "ctrl": "fast-sel-hot-stdby,graceful-conv,susp-individual",
	     "descr": descr,
	     "maxLinks": max_link,
	     "minLinks": min_link,
	     "mode": mode,
	     "name": port_channel
			}
		} 
     } 
    payload_data = json.dumps(config_data)

    apic = '{0}://{1}/'.format(protocol, host)

    auth = dict(aaaUser=dict(attributes=dict(name=username,
                pwd=password)))
    url = apic + 'api/aaaLogin.json'

    authenticate = requests.post(url, data=json.dumps(auth), timeout=2,
                                 verify=False)

    if authenticate.status_code != 200:
        module.fail_json(msg='could not authenticate to apic',
                         status=authenticate.status_code,
                         response=authenticate.text)

    if post_uri.startswith('/'):
        post_uri = post_uri[1:]
    post_url = apic + post_uri

    if get_uri.startswith('/'):
        get_uri = get_uri[1:]
    get_url = apic + get_uri

    if action == 'post':
        req = requests.post(post_url, cookies=authenticate.cookies,
                            data=payload_data, verify=False)
    elif action == 'get':
        req = requests.get(get_url, cookies=authenticate.cookies,
                           data=payload_data, verify=False)

    elif action == 'delete':
        req = requests.delete(post_url, cookies=authenticate.cookies, verify=False)

    response = req.text
    status = req.status_code

    changed = False
    if req.status_code == 200:
        if action == 'post':
            changed = True
        else:
            changed = False
    else:
        module.fail_json(msg='error issuing api request',
                         response=response, status=status)

    results = {}
    results['status'] = status
    results['response'] = response
    results['changed'] = changed

    module.exit_json(**results)

from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
