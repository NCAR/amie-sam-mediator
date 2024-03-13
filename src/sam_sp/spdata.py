MAP_AMIEOrg_from_PeopleExternalOrg_suppl = {
    'Organization': 'name',
    }

MAP_AMIEOrg_from_PeopleExternalOrg_repl = {
    'OrgCode': 'nsfOrgCode',
    'StreetAddress': 'address',
    'City': 'city',
    'State': 'state',
    'Country': 'country',
    'Zip': 'org_zip',
    }

MAP_PeoplePersonSearchParms_from_AMIE = {
    'FirstName': 'firstName',
    'MiddleName': 'middleName',
    'LastName': 'lastName',
}

MAP_AMIEPerson_from_PeoplePerson_suppl = {
    'SitePersonID': None,
    'GlobalID': None,
    'FirstName': 'firstName',
    'MiddleName': 'middleName',
    'LastName': 'lastName',
    'Email': 'email',
    'BusinessPhoneExtension': None,
    'OrgCode': None,

}

MAP_AMIEPerson_from_PeoplePerson_repl = {
    'PersonID': 'username',
    'active': 'active',
    'Username': 'username',
    'Email': 'email',
    'BusinessPhoneNumber': 'phone',
    'RemoteSiteLogin': 'username',
    'Organization': 'org',

}

def supplement_packet_with_spdata(map, packet, spdata):
    out = {}
    for akey in map.keys():
        spkey = map[akey]
        if akey in packet:
            out[akey] = packet[akey]
        elif spkey is not None:
            val = spdata.get(spkey,None)
            if val is not None and val != '':
                out[akey] = val
    for akey in packet.keys():
        if akey not in out:
            out[akey] = packet[akey]
    return out

def replace_packet_with_spdata(map, packet, spdata):
    out = {}
    for akey in map.keys():
        spkey = map[akey]
        if spkey is not None:
            val = spdata.get(spkey,None)
            if val is not None and val != '':
                out[akey] = val
                continue
        if akey in packet:
            out[akey] = packet[akey]
    for akey in packet.keys():
        if akey not in out:
            out[akey] = packet[akey]
    return out

