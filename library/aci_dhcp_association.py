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

module: aci_dhcp_assocation
short_description: Direct access to Cisco ACI APIC API
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
      - The name of the tenant 
      required: yes
   bd_name:
      description:
      - The Bridge Domain name 
      required: yes
   dhcp_name:
      description:
      - Name for the DHCP relay label to be added  
   dhcp_scope:
      description:
      - DHCP Relay label scope can be either tenant or infra 
      default: infra 
      choices: [ tenant, infra ]
   description:
      description:
      - Description for the DHCP
extends_documentation_fragment: aci
'''

EXAMPLES = '''

- name: Add a new DHCP
  aci_dhcp_association:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: Name of the tenant
    bd_name: name of the bridge domain
    dhcp_name: name of the dhcp
    description: Description for the DHCP
    dhcp_scope: tenant
    state: present

- name: Remove a DHCP
  aci_dhcp_association:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: Name of an existing tenant
    bd_name: Name of an exisiting bridge domain
    dhcp_name: Name of the DHCP
    state: absent

- name: Query a DHCP
  aci_dhcp_association:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: Name of an existing tenant
    bd_name: Name of an existing bridge domain
    state: query

- name: Query all DHCPs
  aci_dhcp_association:
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
        tenant_name=dict(type='str'),
        bd_name=dict(type='str'),
        dhcp_name=dict(type="str"),
        dhcp_scope=dict(choices=['tenant', 'infra'], default='infra'),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    tenant_name = module.params['tenant_name']
    bd_name = module.params['bd_name']
    dhcp_name = module.params['dhcp_name']
    dhcp_scope = module.params['dhcp_scope']
    state = module.params['state']
  
    aci = ACIModule(module)

    if (tenant_name,bd_name,dhcp_name) is not None and state == 'present':
        # Work with a specific tenant
        path = 'api/mo/uni/tn-%(tenant_name)s/BD-%(bd_name)s.json' % module.params
    elif state == 'query':
        # Query all tenants
        path = 'api/node/class/dhcpLbl.json'
    elif state == 'absent':
        #delete the DHCP label
        path = 'api/mo/uni/tn-%(tenant_name)s/BD-%(bd_name)s/dhcplbl-%(dhcp_name)s.json' % module.params 
    else:
        module.fail_json(msg="Parameter 'tenant_name', 'bd_name' and 'dhcp_name' are required for state 'absent' or 'present'")

    if state == 'query':
        aci.request(path)
    elif module.check_mode:
        # TODO: Implement proper check-mode (presence check)
        aci.result(changed=True, response='OK (Check mode)', status=200)
    else:
        payload = {"fvBD":{"attributes":{"name": bd_name},"children": [{"dhcpLbl": {"attributes":{"name": dhcp_name,"owner": dhcp_scope }}}]}}
        aci.request_diff(path, payload=json.dumps(payload))

    module.exit_json(**aci.result)
    
if __name__ == "__main__":
    main()
