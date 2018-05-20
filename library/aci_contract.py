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

module: aci_contract
short_description: Manages initial contracts (does not include contract subjs)
description:
    -  Manages contract resource, but does not include subjects although
        subjects can be removed using this module
author: Cisco
requirements:
    - ACI Fabric 1.0(3f)+
notes: Tenant must be exist prior to using this module
options:
    tenant_name:
      description:
      - The name of the tenant
      required: yes
   contract_name:
      description:
      - The name of the contract
      required: yes
   scope:
     description:
     - The scope of a service contract
     required: yes
     default: context
     choices: [ context, application-profile, tenant, global]
   priority:
     description:
     - Qos class
     default: unspecified
     choices: [ 'unspecified','level1','level2','level3']
   target:
     description:
     - Target DSCP
     default: unspecified
   description:
     description:
     - Description for the contract
extends_documentation_fragment: aci
'''

EXAMPLES = '''

- name: Add a new contract
  aci_contract:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    contract_name: Name of the contract
    scope: context
    target: unspecified
    priority: level1
    description: Description for the contract
    state: present

- name: Remove a contract
  aci_contract:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    contract_name: Name of the contract
    state: absent

- name: Query a contract
  aci_contract:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    contract_name: Name of the contract
    state: query

- name: Query all contract
  aci_contract:
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
    argument_spec=aci_argument_spec
    argument_spec.update(
            contract_name=dict(type="str", required=False),
            tenant_name=dict(type="str", required=False),
            priority=dict(choices=['unspecified','level1','level2','level3'],default='unspecified'),
            scope=dict(choices=['context','application-profile','tenant','global'],default='context'),
            target=dict(type="str", required=False, default='unspecified'),
            description=dict(type="str", required=False),
            state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
            method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action']),  # Deprecated starting from v2.6
        )
    

    module = AnsibleModule(
          argument_spec=argument_spec,
        supports_check_mode=True,
    )
   

    contract_name=module.params['contract_name']
    tenant_name=module.params['tenant_name']
    priority=module.params['priority']
    scope=module.params['scope']
    target=module.params['target']
    description=module.params['description']
    state = module.params['state']    
    aci = ACIModule(module)


    if tenant_name is not None and contract_name is not None:
        # Work with a specific tenant
        path = 'api/mo/uni/tn-%(tenant_name)s/brc-%(contract_name)s.json' % module.params
    elif state == 'query':
        # Query all tenants
        path = 'api/node/class/vzBrCP.json'
    else:
        module.fail_json(msg="Parameter 'tenant_name' and 'contract_name' are required for state 'absent' or 'present'")

    if state == 'query':
        aci.request(path)
    elif module.check_mode:
        # TODO: Implement proper check-mode (presence check)
        aci.result(changed=True, response='OK (Check mode)', status=200)
    else:
        payload = {"vzBrCP":{"attributes":{"name":contract_name, "prio":priority,"scope":scope,"targetDscp":target, "descr":description}}}
        aci.request_diff(path, payload=json.dumps(payload))

    module.exit_json(**aci.result)

if __name__ == "__main__":
    main()
