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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---

module: aci_bridge_domain
short_description: Direct access to the Cisco ACI APIC API
description:
    - Offers direct access to the Cisco ACI APIC API
author: 
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
version_added: '2.4'
requirements:
    - ACI Fabric 1.0(3f)+
notes: Tenant should already exist prior to using this module
options:
   tenant_name:
      description:
      - Name of the Tenant 
      required: yes
   bd_name:
      description:
      - Name of the Bridge Domain
      required: yes
   vrf_name:
      description:
      - VRF name to associate to the Bridge Domain
      required: yes
   arp_flooding:
      description:
      - Enable or Disable ARP_Flooding
      default: yes
      choices: [ yes, no ]
   l2_unkwown_unicast: 
      description:
      - 
      default: proxy
      choices: [ proxy, flood ]
   l3_unknown_multicast:
      description:
      -
      default: flood
      choices: [ flood, opt-flood ]
   multi_dest:
      description:
      -
      default: bd-flood
      choices: [ bd-flood, drop, encap-flood ]
   gateway_ip:
      description:
      - Gateway IP for subnet
   subnet_mask:
      description:
      - Value of the subnet mask 
   scope:
      description:
      - Subent Scope - can be private or public and shared 
      default: private
     
'''

EXAMPLES =  '''

- name: Add a new bridge domain
  aci_bridge_domain:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    bd_name: Name of the bridge domain 
    vrf_name: Name of the context  
    arp_flooding: yes
    l2_unknown_unicast: proxy
    l3_unknown_multicast: flood
    multi_dest: bd-flood
    gateway_ip: 10.10.10.1
    subnet_mask: 24
    scope: 'public,shared'
    state: present

- name: Remove bridge domain
  aci_bridge_domain:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    bd_name: Name of the bridge domain
    vrf_name: Name of the context
    state: absent

- name: Query a bridge domain
  aci_bridge_domain :
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    bd_name: Name of the bridge domain
    vrf_name: Name of the context
    state: query

- name: Query all Bridge Domains
  aci_bridge_domain:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    state: query

'''
RETURN = r'''
status:
  description: The status code of the http request
  returned: upon making a successful GET, POST or DELETE request to the APIC
  type: int
  sample: 200
response:
  description: Response text returned by APIC
  returned: when a HTTP request has been made to APIC
  type: string
  sample: '{"totalCount":"0","imdata":[]}'

'''

import json

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule

def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        tenant_name=dict(type='str', required=True),
        bd_name=dict(type='str', required=True),
        arp_flooding=dict(choices=['yes','no'], default="yes"),
        l2_unknown_unicast=dict(choices=['proxy','flood'], default='proxy'),
        l3_unknown_multicast=dict(choices=['flood','opt-flood'], default='flood'),
        multi_dest=dict(choices=['bd-flood','drop','encap-flood'], default='bd-flood'),
        vrf_name=dict(type='str'),
        gateway_ip=dict(type='str', default=0, required=False),
        subnet_mask=dict(type='str', default=0, required=False),
        scope=dict(type='str',default='private'),
        host=dict(required=True),
        username=dict(type='str', default='admin'),
        password=dict(type='str'),
        protocol=dict(choices=['http', 'https'], default='http'),
        )
  
    module = AnsibleModule(
       argument_spec=agrument_spec,
       supports_check_mode=True,
    )

    tenant_name = module.params['tenant_name']
    bd_name = module.params['bd_name']
    arp_flooding = module.params['arp_flooding']
    l2_unknown_unicast = module.params['l2_unknown_unicast']
    l3_unknown_multicast = module.params['l3_unknown_multicast']
    multi_dest = module.params['multi_dest']
    vrf_name = module.params['vrf_name']
    state = module.params['state']

    #subnet
    gateway_ip = module.params['gateway_ip']
    subnet_mask = module.params['subnet_mask']
    if gateway_ip != 0  and subnet_mask != 0:
       ip = gateway_ip + "/" + subnet_mask
    else:
       ip = ''
    scope = module.params['scope']
 
    aci = ACIModule(module)
    
    if tenant_name is not None and bd_name is not None and vrf_name is not None:
       # Work with specific bridge domain 
       path = 'api/mo/uni/tn-%(tenant_name)s/BD-%(bd_name)s.json' % module.params
    elif state == 'query':
       # query all bridge domains
       path = 'api/node/class/fvBD.json'
    else:
       module.fail_json("Parameter 'tenant_name' is required for state 'absent' or 'present'")

    config_data =  {
         "fvBD": {
             "attributes": {
                  "descr": "test",
                  "arpFlood": arp_flooding,
                  "unkMacUcastAct":l2_unknown_unicast,
                  "unkMcastAct": l3_unknown_multicast,
                  "multiDstPktAct": multi_dest
               },
              "children":[{
                   "fvRsCtx": {
                      "attributes": {
                          "tnFvCtxName": vrf_name
                         }
                      }
                  }
                ]

           }
     }

    subnet_config_data =  {
                   "fvSubnet":{
                      "attributes":{
                          "ip": ip,
                          "scope": scope
                        }
                    }
                  }


    payload_data = json.dumps(config_data)
    subnet_payload_data = json.dumps(subnet_config_data)

    if action == 'post':
        req = requests.post(post_url, cookies=authenticate.cookies,
                            data=payload_data, verify=False)
        if gateway_ip != 0:
           get_bd = requests.get(post_url, cookies=authenticate.cookies,
                                 data=payload_data, verify=False)
           data =json.loads(get_bd.text)
           count = data['totalCount']
           count = int(count)
           bridge_domain_list = []
           if get_bd.status_code == 200:
              for name in range(0,count):
                  bd = data['imdata'][name]['fvBD']['attributes']['name']
                  bridge_domain_list.append(bd)
                  if bd_name in bridge_domain_list:
                      subnet_req = requests.post(post_url, cookies=authenticate.cookies,
                                                 data=subnet_payload_data, verify=False)
                  else:
                       module.fail_json(msg='Subnet creation failed.')
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
        module.fail_json(msg=response,
                         response=response, status=status)

    results = {}
    results['status'] = status
    results['response'] = response
    results['changed'] = changed
    module.exit_json(**results)

from ansible.module_utils.basic import *
if __name__ == '__main__':
   main()
