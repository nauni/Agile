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

module: aci_contract_subjects
short_description: Manages initial contract subjects(does not include contracts)
description:
    -  Manage contract subjects with this module
author: 
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
version_added: '2.4'
requirements:
    - ACI Fabric 1.0(3f)+
notes: Tenant must be exist prior to using this module
options:
   tenant_name:
     description
     - The name of the tenant 
     required: yes
   subject_name:
     description:
     - The contract subject name
     required: yes
   contract_name:
     description:
     - the name of the Contract 
     required: yes
   reverse_filter:
     description:
     - Select or De-select reverse filter port option
     default: no
     choices: [ yes, no ]
   priority:
     description:
     - Qos class 
     default: unspecified
     choices: [ unspecified, level1, level2, level3 ]
   target:
     description:
     - Target DSCP
     default: unspecified
   filter_name:
     description:
     - Filter Name
   directive:
     description:
     - Directive for filter  (can be none or log)
   description:
     description:
     - Description for the contract subject
extends_documentation_fragment: aci
'''

EXAMPLES = r'''

- name: Add a new contract subject
  aci_contract_subjects:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: Name of the tenant
    contract_name: name of the contract
    subject_name: name of the contract subject
    description: Description for the contract subject
    reverse_filter: yes
    priority: level1
    target: unspecified
    filter_name: name of the filter
    directive: log
    state: present

- name: Remove a contract subject
  aci_contract_subjects:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    contract_name: name of the contract
    subject_name: name of the subject
    state: absent

- name: Query a contract subject
  aci_contract_subjects:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: production
    contract_name: name of the contract
    subject_name: name of the contract subject
    state: query

- name: Query all contract subjects
  aci_contract_subjects:
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
            contract_name=dict(type="str"),
            subject_name=dict(type="str", required=False),
            tenant_name=dict(type="str", required=False),
            priority=dict(choices=[ 'unspecified','level1','level2','level3'],default='unspecified', required=False),
            reverse_filter=dict(choices=['yes','no'], required=False, default='yes'),
            target=dict(type="str", required=False, default='unspecified'),
            description=dict(type="str", required=False),
            filter_name=dict(type="str", required=False),
            directive=dict(choices=['none', 'log'], required=False, default='none'),
        )

    module = AnsibleModule(
       argument_spec=argument_spec,
       supports_check_mode=True,
    )

    subject_name=module.params['subject_name']
    tenant_name=module.params['tenant_name']
    priority=module.params['priority']
    reverse_filter=module.params['reverse_filter']
    target=module.params['target']
    description=module.params['description']
    contract_name= module.params['contract_name']
    filter_name = module.params['filter_name']
    directive = module.params['directive']
    state = module.params['state']

    if directive == "none":
        directive = ""
     
    aci = ACIModule(module)

    if (tenant_name,contract_name,subject_name) is not None:
        # Work with a specific tenant
        path = 'api/mo/uni/tn-%(tenant_name)s/brc-%(contract_name)s/subj-%(subject_name)s.json' % module.params
    elif state == 'query':
        # Query all tenants
        path = 'api/node/class/vzSubj.json'
    else:
        module.fail_json(msg="Parameter 'tenant_name', 'contract_name' and 'subject_name ' are required for state 'absent' or 'present'")

    if state == 'query':
        aci.request(path)
    elif module.check_mode:
        # TODO: Implement proper check-mode (presence check)
        aci.result(changed=True, response='OK (Check mode)', status=200)
    else:
        payload =  {"vzSubj":{"attributes":{"name": subject_name,"prio": priority,"revFltPorts": reverse_filter,"targetDscp": target,"descr":description },"children":[{"vzRsSubjFiltAtt":{"attributes":{"directives": directive,"tnVzFilterName": filter_name}}}]}}
        aci.request_diff(path, payload=json.dumps(payload))

    module.exit_json(**aci.result)

if __name__ == "__main__":
    main()

