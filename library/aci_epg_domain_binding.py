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

module: aci_epg_domain_binding
short_description: Direct access to the Cisco ACI APIC API
description:
    - Offers direct access to the Cisco ACI APIC API
author: 
- Swetha Chunduri(@schunduri)
- Dag Wieers (@dagwieers)
version_added: '2.4'
requirements:
    - ACI Fabric 1.0(3f)+
notes:
    - Tenant, application profile and EPG must exist prior to using this module
options:
    tenant_name:
      description:
      - The name of an existing Tenant 
      required: yes
    application_profile_name:
      description:
      - The name of an existing Application Profile 
      required: yes
    epg_name:
      description:
      - The name of an existing EPG 
      required: yes
    domain:
      description:
      - Dictates domain to be used
      default: phys
      choices: [ phys, vmm ]
    domain_profile:
      description:
      - Dictates domain profile to be attached
      required: yes
    vlan_mode:
      description:
      - Dynamic | Static
      default: dynamic
      choices: [ dynamic, static ]
    encap:
      description:
      - Vlan encapsulation
      required: yes
    deploy_immediacy:
      description:
      - On Demand | Immediate
      default: on-demand
      choices: [ on-demand, immediate ]
    resolution_immediacy:
      description:
      - On Demand | Immediate | Pre-Provision
      default: on-demand
      choices: [ on-demand, immediate, pre-provision ]
    netflow:
      description:
      - Enabled | Disabled
      default: enabled
      choices: [ enabled, disabled ]
extends_documentation_fragment: aci
'''

EXAMPLES = '''

- name: Add a new Domain binding
  aci_epg_domain_binding:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: Name of an existing tenant
    application_profile_name: Name of an existing application profile 
    epg_name: Name of the End point Group
    domain: Name of domain (vmm or phy)
    domain_profile: Name of the domain profile
    encap: vlan-1 #only applicable when vlan_mode is static in vmm domain binding
    deploy_immediacy: immediacy 
    resolution_immediacy: on-demand
    vlan_mode: static   #only for vmm domain binding
    state: present

- name: Remove a domain binding
  aci_epg_domain_binding:
    hostname: apic
    username: admin
    password: SomeSecretPassword
    tenant_name: Name of an existing tenant
    application_profile_name: Name of an existing application profile
    epg_name: Name of an exisiting EPG
    domain: Name of the domain (vmm or phy)
    domain_profile: Name of the domain profile
    state: absent


- name: Query all domains
  aci_epg_domain_bindiing:
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
            application_profile_name=dict(type='str'),
            epg_name=dict(type='str'),
	    domain=dict(choices=['phys', 'vmm'], default='phys'),
	    domain_profile=dict(type='str'),
            vlan_mode=dict(choices=['dynamic','static'],default = 'dynamic'),
            encap=dict(type='str'),
            deploy_immediacy=dict(choices=['immediate','on-demand'], default='on-demand'),
            resolution_immediacy=dict(choices=['immediate','on-demand', 'pre-provision'], default = 'on-demand'),
            netflow=dict(choices=['enabled','disabled'], default = 'disabled'),
    )

    module = AnsibleModule(
          argument_spec=argument_spec,
          supports_check_mode=True,
    ) 

    tenant_name = module.params['tenant_name']
    application_profile_name  = module.params['application_profile_name']
    epg_name = module.params['epg_name']
    vlan_mode = module.params['vlan_mode']
    netflow= module.params['netflow']
    domain = module.params['domain']
    if domain == 'vmm':
       domain = 'vmmp-VMware/dom'
    domain_profile = module.params['domain_profile']
    encap = module.params['encap']
    deploy_immediacy = module.params['deploy_immediacy']
    if deploy_immediacy == 'on-demand':
       deploy_immediacy = 'lazy'
    resolution_immediacy = module.params['resolution_immediacy']
    if resolution_immediacy == 'on-demand':
       resolution_immediacy = 'lazy'

    aci = ACIModule(module)

    if (tenant_name,application_profile_name,epg_name,domain,domain_profile) is not None:
        # Work with a specific managed object
        path = '/api/mo/uni/tn-%(tenant_name)s/ap-%(application_profile_name)s/epg-%(epg_name)s/rsdomAtt-[uni/%(domain)s-%(domain_profile)s].json' % module.params
    elif state == 'query':
        # Query all profiles
        path = 'api/node/class/fvRsDomAtt.json'
    else:
        module.fail_json(msg="Parameter 'tenant_name','application_profile_name','epg_name','domain' and 'domain_profile' is required for state 'absent' or 'present'")


    payload = {"fvRsDomAtt":{"attributes": {"encap" : 'vlan-'+encap,"instrImedcy": deploy_immediacy,"netflowPref" : netflow,"resImedcy": resolution_immediacy}}}
    if domain == "vmmp-VMware/dom" and vlan_mode == 'dynamic':
        del config_data['fvRsDomAtt']['attributes']['encap']

    elif domain == "phys":
        del config_data['fvRsDomAtt']['attributes']['netflowPref']
    else:
        module.fail_json(msg= " Error in JSON payload "

    if state == "query":
        aci.request(path)
    elif module.check_mode:
        # TODO: Implement proper check-mode (presence check)
        aci.result(changed=True, response='OK (Check mode)', status=200)
    else:
        aci.request_diff(path, payload=json.dumps(payload))

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()
