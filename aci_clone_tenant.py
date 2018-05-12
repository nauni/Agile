#!/usr/bin/env python
#
"""

     Copyright (c) 2016 World Wide Technology, Inc. 
     All rights reserved. 


     Revision history:

     24 January 2016  |  1.0 - initial release
     25 January 2016  |  1.1 - further tweeks on XML to repost
     26 January 2016  |  1.2 - only delete statsHierColl
      2 Febr    2016  |  2.0 - added ihost and ohost to move between fabrics

"""
DOCUMENTATION = '''

---

module: aci_clone_tenant
author: Joel W. King, World Wide Technology
version_added: "2.0"
short_description: Clones a tenant using the northbound interface of a Cisco ACI controller (APIC)

description:
    - This module creates a new tenant based on a reference, or template tenant. You specify the new tenant name and a description.
      All references to the template tenant are changed to refer to the new tenant name. This module can move configurations between
      separate ACI fabrics by specifing a different host name or IP address for ihost and ohost.

requirements:
    - AnsibleACI module

options:
    ihost:
        description:
            - The IP address or hostname of the APIC where the template exists
        required: true
    ohost:
        description:
            - The IP address or hostname of the APIC to write the clone 
        required: true
    username:
        description:
            - Login username of the APIC
        required: true
    password:
        description:
            - Login password of the APIC
        required: true
    descr:
        description:
            - A string to populate in the descr field of the new tenant
        required: true
    template:
        description:
            - The managed object name of the reference, or template tenant
        required: true
    debug:
        description:
            - A switch to enable debug. Use a value of 'on' to enable.
        required: false

'''

EXAMPLES = '''

  ansible localhost -m aci_clone_tenant -a "descr=foo tenant=xStart template=mediaWIKI ihost=10.255.139.149 ohost=10.255.139.149 username=kingjoe password=redacted debug=on"


  - name: Clone a Tenant
    aci_clone_tenant:
     ihost:  "{{inventory_hostname}}"
     ohost:  "{{inventory_hostname}}"
     username:  kingjoe
     password: "{{password}}"
     descr: Example of cloning a tenant from a template joel.king
     template: mediaWIKI
     tenant: xStart



'''

#
import sys
import time
import xml.etree.ElementTree as ET
import logging

try:
    import AnsibleACI
except ImportError:
    sys.path.append("/usr/share/ansible")
    import AnsibleACI


def get_tenant(cntrl, tenant):
    "query the controller for the tenant, the config and subtree"

    retcode = cntrl.aaaLogin()
    if retcode != 200:
        return "get_tenant: Unable to login to controller", retcode

    cntrl.setgeneric_URL("%s://%s" + "/api/mo/uni/tn-%s.xml?rsp-subtree=full&rsp-prop-include=config-only" % tenant)
    retcode = cntrl.genericGET()
    get_content = cntrl.get_content()
    cntrl.aaaLogout()

    return get_content, retcode



def post_tenant(cntrl, xml):
    " post the modified xml to create a new tenant from the template"
    
    retcode = cntrl.aaaLogin()
    if retcode != 200:
        return "post_tenant: Unable to login to controller", retcode
    cntrl.setgeneric_XML(xml)
    cntrl.setgeneric_URL("%s://%s/api/mo/uni.xml?rsp-subtree=modified")
    retcode = cntrl.genericPOST()
    post_content = cntrl.get_content()
    cntrl.aaaLogout()

    return post_content, retcode



def get_changed_flag(content):
    "determine if we have change the APIC configuration"

    changed_msg = ['status="created"', 'status="modified"', 'status="deleted"']
    changed = False
    for item in changed_msg:
        if item in content:
            return True
    return False



def modify_xml(xml_string, template, new_tenant_name, description):
    """ 
        eliminate the imdata wrapper the drawing configuration and add a description to the tenant
        to indicate what tenant it was configured from and when.
    """
    xml_string = remove_imdata(xml_string)
    # need to replace all references of the template tenant with the new tenant name
    xml_string = xml_string.replace('uni/tn-%s' % template ,'uni/tn-%s' % new_tenant_name)

    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError:
        return  "The server returned status code of 200, but no data, typical of missing template tenant"

    # Set the name of the new tenant, and add a description
    root.attrib['descr'] = description
    root.attrib['name'] = new_tenant_name

    # Delete all the drawCont 
    for item in root.findall('drawCont'):    
        root.remove(item)

    # Delete statsHierColl out of monEPGPol, APIC will not permit these to be updated
    for monEPGPol in root.findall('monEPGPol'):
        for statsHierColl in monEPGPol.findall('statsHierColl'):
            monEPGPol.remove(statsHierColl)

    return ET.tostring(root, encoding="us-ascii", method="xml")



def remove_imdata(xml):
    """ remove the imdata tag, the tag is in the form of <imdata totalCount="0"></imdata> 
        the totalCount should always be 1, but let element tree tell us for certain
    """
    root = ET.fromstring(xml)
    totalCount = root.attrib["totalCount"]
    xml = xml.replace('<imdata totalCount="%s">' % totalCount, "")
    xml = xml.replace('</imdata>',"")
    return xml



def get_connection_object(host, username, password, debug):
    " Create an Connection object for the controller and set parameters "

    cntrl = AnsibleACI.Connection()
    cntrl.setcontrollerIP(host)
    cntrl.setUsername(username)                               
    cntrl.setPassword(password)
    cntrl.setDebug(debug)
    return cntrl


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():

    module = AnsibleModule(
        argument_spec = dict(
            template = dict(required=True),
            descr = dict(required=True),
            tenant = dict(required=True),
            ihost = dict(required=True),
            ohost = dict(required=True),
            username = dict(required=True),
            password  = dict(required=True),
            debug = dict(required=False, default=False, type='bool')
         ),
        check_invalid_arguments=False,
        add_file_common_args=True
    )
    
    # We expect the same username and password on both fabrics if moving between fabrics
    username = module.params["username"] 
    password = module.params["password"] 
    debug = module.params["debug"]
    
    # Connect to the controller where the template resides
    cntrl = get_connection_object(module.params["ihost"], username, password, debug)
    xml_string, retcode = get_tenant(cntrl, module.params["template"])
    
    if retcode == 200:
        # modify and create the cloned template on the target APIC
        new_xml = modify_xml(xml_string, module.params["template"], module.params["tenant"], module.params["descr"])
        cntrl = get_connection_object(module.params["ohost"], username, password, debug)
        content, retcode = post_tenant(cntrl, new_xml)
        if retcode == 200:
        	module.exit_json(changed=get_changed_flag(content), content=retcode)
        else:
            module.fail_json(msg="%s %s %s %s" % (retcode, "failed to post tenant", module.params["tenant"], xml_string))
    else:
    	module.fail_json(msg="%s %s %s %s" % (retcode, "failed to get tenant", module.params["tenant"], xml_string))
  
    return 


from ansible.module_utils.basic import *
if __name__ == '__main__':
	main()
