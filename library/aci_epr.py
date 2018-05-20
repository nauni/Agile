#!/usr/bin/python

DOCUMENTATION = '''
---

module: aci_epr
short_description: Direct access to the APIC API
description:
    - Offers direct access to the APIC API
author: Cisco
requirements:
    - ACI Fabric 1.0(3f)+
notes:
    - Tenant should already exist
options:
    action:
        description:
            - post, get, or delete
        required: true
        default: null
        choices: ['post','get', 'delete']
        aliases: []
    tenant_name:
        description:
            - Tenant Name
        required: true
        default: null
        choices: []
        aliases: []
    epr_name:
        description:
            - End point retention policy name
        required: true
        default: null
        choices: []
        aliases: []
    bounce_age:
        description:
            - Bounce Entry Aging Interval (range 150secs - 65535secs)
        required: true
        default: 630
        choices: []
        aliases: []
    hold_interval:
        description:
            - Hold Interval (range 5secs - 65535secs)
        required: true
        default: 300
        choices: []
        aliases: []
    local_ep_interval:
        description:
            - Local end point Aging Interval (range 120secs - 65535secs)
        required: true
        default: 900
        choices: []
        aliases: []
    remote_ep_interval:
        description:
            - Remote end point Aging Interval (range 120secs - 65535secs)
        required: true
        default: 300
        choices: []
        aliases: []
     move_frequency:
        description:
            - Move frequency per second (range 0secs - 65535secs)
        required: true
        default: 256
        choices: []
        aliases: []
    descr:
        description:
	    - Description for the End point rentention policy
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

    aci_epr:
        action: "{{ action }}"
        tenant_name: "{{ tenant_name }}"
        epr_name: "{{ epr_name }}"
        bounce_age: "{{ bounce_age }}"
        hold_interval: "{{ hold_interval }}"
        local_ep_interval: "{{ local_ep_interval }}"
        remote_ep_interval: "{{ remote_ep_interval }}"
        move_frequency: "{{ move_frequency }}"
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
            action=dict(choices=['get', 'post', 'delete'], required=False),
            tenant_name=dict(type='str', required = True),
            epr_name=dict(type='str', required = True),
            bounce_age=dict(type='int', default = '630'),
            hold_interval=dict(type='int', default = '300'),
            local_ep_interval=dict(type='int', default = '900'),
            remote_ep_interval=dict(type='int', default = '300'),
            descr=dict(type='str'),
            move_frequency=dict(type='int', default = '256'),
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

    tenant_name = module.params['tenant_name'] 
    epr_name = module.params['epr_name']
    bounce_age = module.params['bounce_age']
    bounce_age = str(bounce_age)
    descr = module.params['descr']
    descr =str(descr)
    hold_interval= module.params['hold_interval']
    hold_interval = str(hold_interval)
    local_ep_interval = module.params['local_ep_interval']
    local_ep_interval = str(local_ep_interval)
    move_frequency= module.params['move_frequency']
    move_frequency = str(move_frequency)
    remote_ep_interval = module.params['remote_ep_interval']
    remote_ep_interval = str(remote_ep_interval)

    post_uri = '/api/node/mo/uni/tn-'+ tenant_name + '/epRPol-' +epr_name+ '.json'
    get_uri = '/api/node/class/fvEpRetPol.json'

    config_data = {
       "fvEpRetPol": {
       "attributes": {
         "bounceAgeIntvl": bounce_age,
         "descr": descr,
         "holdIntvl": hold_interval,
         "localEpAgeIntvl": local_ep_interval,
         "moveFreq": move_frequency,
         "name": epr_name,        
         "remoteEpAgeIntvl": remote_ep_interval

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
        req = requests.delete(post_url, cookies=authenticate.cookies, data=payload_data, verify=False)

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
