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

module: aci_context
short_description: Manage private networks, contexts, in Cisco ACI fabric
description:
    -  Offers ability to manage private networks. Each context is a private network associated to a tenant, i.e. VRF
author: 
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
version_added: '2.4'
requirements:
    - ACI Fabric 1.0(3f)+
notes: Tenant must be exist prior to using this module
options:
  tenant_name:
      description:
      - The name of the Tenant that must contain the VRF
      required: yes
   vrf_name:
      description:
      - The name of the Context
      required: yes
   policy_control_direction:
      description:
      - Policy Control Direction
      default: ingress
      choices: [ egress, ingress ]
   policy_control_preference:
      description:
      - Policy Control Preference
      default: enforced
      choices: [ enforced, unenforced ]
   description:
      description:
      - Description for the Context
   state:
      description:
      - present, absent, query
      default: present
      choices: [ absent, present, query ]
extends_documentation_fragment: aci

'''

EXAMPLES = '''

- name: Add a new VRF 
  aci_context:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    vrf_name: Name of the context 
    description: Description for Context
    policy_control_preference: unenforced
    policy_control_direction: egress
    state: present

- name: Remove a VRF
  aci_context:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    vrf_name: Name of the context
    state: absent

- name: Query a VRF
  aci_context:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    vrf_name: Name of the context
    state: query

- name: Query all VRFs
  aci_context:
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
            vrf_name=dict(type="str", required=False),
            tenant_name=dict(type="str", required=False),
            description=dict(type="str", required=False),
            policy_control_preference=dict(choices=['enforced','unenforced'], required=False, default='enforced'),
            policy_control_direction=dict(choices=['egress','ingress'], required=False, default='ingress'),
            state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
            method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action']),  # Deprecated starting from v2.6
        )

     module = AnsibleModule(
            argument_spec=argument_spec,
            supports_check_mode=True,
     )

     vrf_name = module.params['vrf_name']
     tenant_name = module.params['tenant_name']
     description = module.params['description']
     policy_control_direction = module.params['policy_control_direction']
     policy_control_preference = module.params['policy_control_preference']
     state = module.params['state']

     aci = ACIModule(module)
  
     if (tenant_name and vrf_name) is not None:
       # Work with a specific tenant and context
        path = '/api/mo/uni/tn-%(tenant_name)s/ctx-%(vrf_name)s.json' % module.params
     elif state == 'query':
        # Query all the contexts
        path = '/api/node/class/fvCtx.json'
     else:
        module.fail_json(msg="Parameter 'tenant_name' and 'vrf_name' are  required for state 'absent' or 'present'")
   
     if state == 'query':
         aci.request(path)
     elif module.check_mode:
         # TODO: Implement proper check-mode (presence check)
         aci.result(changed=True, response='OK (Check mode)', status=200)
     else:
         payload = {"fvCtx":{"attributes":{"name":vrf_name, "descr":description, "pcEnfDir":policy_control_direction, "pcEnfPref":policy_control_preference }}}
         aci.request_diff(path, payload=json.dumps(payload))

     module.exit_json(**aci.result)

if __name__ == "__main__":
    main()
