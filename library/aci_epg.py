#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---

module: aci_epg
short_description: Manage top level application network profile objects
description:
    -  Manage top level application network profile object, i.e. this does
      not manage EPGs.
author: Cisco
requirements:
    - ACI Fabric 1.0(3f)+
notes: Tenant must be exist prior to using this module
options:
    action:
        description:
            - post or get
        required: true
        default: null
        choices: ['post','get']
        aliases: []
    tenant_name:
        description:
            - Tenant Name
        required: true
        default: null
        choices: []
        aliases: []
   app_profile_name:
        description:
            -Application Profile Name
        required: true
        default: null
        choices: []
        aliases: []
   epg_name:
        description:
            -End Point Group Name
        required: true
        default: null
        choices: []
        aliases: []
   bd_name:
        description:
            - Name of the Bridge Domain being associated to the EPG
        required: true
        default: null
        choices: []
        aliases: []     
   priority:
        description:
            - Qos class 
        required: false
        default: unspecified
        choices: ['level1', 'level2', 'level3', 'unspecified']
        aliases: []
   intra_epg_isolation:
        description:
            - Intra EPG Isolation
        required:false
        default: unenforced
        choices: ['enforced', 'unenforced']
        aliases: []
    descr:
        description:
            - Description for the AEP
        required: false
        default: null
        choices: []
        aliases: []
    contract_type:
        description:
            - Type of Contract being associated with the EPG[provider, consumer or both]
        required: false
        default: null
        choices: ['provider','consumer', 'both']
        aliases: []
    contract_name_provider:
        description:
            - Name of the provider contract
        required: false
        default: null
        choices: []
        aliases: []
    contract_name_consumer:
        description:
            - Name of the consumer contract
        required: false
        default: null
        choices: []
        aliases: [] 
    priority_provider:
        description:
            - Qos value for the provider contract
        required: false
        default: 'unspecified'
        choices: ['level1','level2', 'level3', 'unspecified']
        aliases: []
    priority_consumer:
        description:
            - Qos value for the consumer contract
        required: false
        default: 'unspecified'
        choices: ['level1','level2', 'level3', 'unspecified']
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
        aliases:[]                                                                  
    protocol:
        description:
            - Dictates connection protocol to use
        required: false
        default:'https'
        choices: ['http', 'https']
        aliases: []
'''

EXAMPLES = '''

    aci_epg:
       action: "{{ action }}"
       epg_name: ""{{ epg_name }}"
       app_profile_name: "{{ app_profile_name }}"
       tenant_name: "{{ tenant_name }}"
       bd_name: "{{ bd_name }}"
       priority: "{{ priority }}"
       contract_type: "{{ contract_type }}"
       contract_name_provider: "{{ contract_name_provider }}"
       contract_name_consumer: "{{ contract_name_consumer }}"
       priority_provider: "{{ priority_provider }}"
       priority_consumer: "{{ priority_consumer }}"
       intra_epg_isolation: "{{ intra_epg_isolation }}"
       descr: "{{ descr }}"
       host: "{{ inventory_hostname }}"
       username: "{{ user }}"
       password: "{{ pass }}"
       protocol: "{{ protocol }}"

'''


import socket
import json
import requests

def main():

    ''' Ansible module to take all the parameter values from the playbook '''
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(choices=['post', 'get', 'delete']),
            host=dict(required=True),
            username=dict(type='str', default='admin'),
            password=dict(type='str'),
            protocol=dict(choices=['http', 'https'], default='https'),
            epg_name=dict(type="str"),
            contract_name_provider=dict(type="str"),
            contract_name_consumer = dict(type="str"),
            contract_type=dict(choices=['provider','consumer','both'], required=False),
            priority_provider = dict(choices=['level1','level2','level3','unspecified'], required=False, default='unspecified'),
            priority_consumer = dict(choices=['level1','level2','level3','unspecified'], required=False, default='unspecified'),
            bd_name=dict(type="str"),
            app_profile_name=dict(type="str"),
            tenant_name=dict(type="str"),
            descr=dict(type="str", required=False),
            priority=dict(choices=['level1','level2','level3','unspecified'], required=False, default='unspecified'),
            intra_epg_isolation=dict(choices=['enforced','unenforced'], default='unenforced'),
        ),
        supports_check_mode=False
    )

    epg_name=module.params['epg_name']
    app_profile_name=module.params['app_profile_name']
    tenant_name=module.params['tenant_name']
    bd_name = module.params['bd_name']
    descr=module.params['descr']
    descr=str(descr)
    contract_name_provider = module.params['contract_name_provider']
    contract_name_consumer = module.params['contract_name_consumer']
    contract_type = module.params['contract_type']
    priority_provider = module.params['priority_provider']
    priority_consumer = module.params['priority_consumer']
    priority = module.params['priority']
    descr = str(descr)
    priority=module.params['priority']
    priority = str(priority)
    intra_epg_isolation=module.params['intra_epg_isolation']
    username = module.params['username']
    password = module.params['password']
    protocol = module.params['protocol']
    host = socket.gethostbyname(module.params['host'])
    action = module.params['action']
    
    ''' Config payload to enable the physical interface '''
    if contract_type == "provider":
       config_data = {
        "fvAEPg":{
          "attributes":{
             "name": epg_name,
             "descr": descr,
             "prio": priority,
             "pcEnfPref": intra_epg_isolation
                  },
            "children": [{
                    "fvRsBd":{
                      "attributes":{
                          "tnFvBDName": bd_name
                          }
                     }
                },
                {
                "fvRsProv":{
                  "attributes":{
                    "tnVzBrCPName": contract_name_provider,
                    "prio" : priority_provider
                    }
                  } 
                }

           ]
       }
    }
    elif contract_type == "consumer":
        config_data = {
            "fvAEPg": {
                "attributes": {
                    "name": epg_name,
                    "descr": descr,
                    "prio": priority,
                    "pcEnfPref": intra_epg_isolation
                },
                "children": [{
                    "fvRsBd": {
                        "attributes": {
                            "tnFvBDName": bd_name
                        }
                    }
                },
                 {
                    "fvRsCons": {
                         "attributes": {
                              "tnVzBrCPName": contract_name_consumer,
                               "prio": priority_consumer
                            }
                        }
                    }

                ]
            }
        }
    elif contract_type == "both":
       config_data = {
            "fvAEPg": {
                "attributes": {
                    "name": epg_name,
                    "descr": descr,
                    "prio": priority,
                    "pcEnfPref": intra_epg_isolation
                },
                "children": [{
                    "fvRsBd": {
                        "attributes": {
                            "tnFvBDName": bd_name
                        }
                    }
                },
                    {
                        "fvRsProv": {
                            "attributes": {
                                "tnVzBrCPName": contract_name_provider,
                                "prio": priority_provider
                        }
                    }
            },
            {
                "fvRsCons": {
                    "attributes": {
                        "tnVzBrCPName": contract_name_consumer,
                        "prio": priority_consumer
                    }
                }
            }

          ]
        }
    }
    else:
        config_data = {
            "fvAEPg": {
                "attributes": {
                    "name": epg_name,
                    "descr": descr,
                    "prio": priority,
                    "pcEnfPref": intra_epg_isolation,
                },
                "children": [{
                    "fvRsBd": {
                        "attributes": {
                            "tnFvBDName": bd_name,
                        }
                    }
                }
                ]
            }
      }

    post_uri ='api/mo/uni/tn-'+tenant_name+'/ap-'+app_profile_name+'/epg-'+epg_name+'.json'
    get_uri = 'api/node/class/fvAEPg.json'

    
    payload_data = json.dumps(config_data)

    ''' authentication || || Throw an error otherwise'''
    apic = '{0}://{1}/'.format(protocol, host)
    auth = dict(aaaUser=dict(attributes=dict(name=username, pwd=password)))
    url=apic+'api/aaaLogin.json'
    authenticate = requests.post(url, data=json.dumps(auth), timeout=2, verify=False)

    if authenticate.status_code != 200:
        module.fail_json(msg='could not authenticate to apic', status=authenticate.status_code, response=authenticate.text)

    ''' Sending the request to APIC '''
    if post_uri.startswith('/'):
        post_uri = post_uri[1:]
    post_url = apic + post_uri

    if get_uri.startswith('/'):
        get_uri = get_uri[1:]
    get_url = apic + get_uri

    if action == 'post':
        req = requests.post(post_url, cookies=authenticate.cookies, data=payload_data, verify=False)

    elif action == 'get':
        req = requests.get(get_url, cookies=authenticate.cookies, data=payload_data, verify=False)

    elif action == 'delete':
        req = requests.delete(post_url, cookies=authenticate.cookies, data=payload_data, verify=False)
    ''' Check response status and parse it for status || Throw an error otherwise '''
    response = req.text
    status = req.status_code
    changed = False

    if req.status_code == 200:
        if action == 'post':
            changed = True
        else:
            changed = False

    else:
        module.fail_json(msg='error issuing api request',response=response, status=status)

    results = {}
    results['status'] = status
    results['response'] = response
    results['changed'] = changed
    module.exit_json(**results)

from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
