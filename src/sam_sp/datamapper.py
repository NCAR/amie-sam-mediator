
COPY_SRC_OR_ADD_NONE = 0
COPY_SRC_OR_ADD_BLANK = 1
COPY_SRC_IF_SRC_SET = 2
COPY_SRC_IF_SRC_SET_TARG_UNSET = 4

#
# The following dict describes how data from a source dict is used to update a
# copy of a target dict (see the map_data() function). Source and target
# objects are assumed to be dictionaries. The mappings identify which source
# values should be copied, and how the key names should be mapped.
#
# Top level keys identify the objects the mappings apply to. Most mappings
# describe how SAM/PeopleDB objects map to AMIE Packets.
#
# At the next level, keys identify how to set entries in the target dict; there
# are four possible values:
#  COPY_SRC_OR_ADD_NONE - the source key is always added to the target dict,
#      even when the source value is not set; if the key is missing from the
#      source, a value of None is added to the target;
#  COPY_SRC_OR_ADD_BLANK - the source key is always added to the target dict
#      with a value, even when the source value is not set; if the key is
#      missing from the source, an empty string is added to the target;
#  COPY_SRC_IF_SRC_SET - if the source key is associated with a value in the
#      source, that value is copied to the target
#  COPY_SRC_IF_SRC_SET_TARG_UNSET - if the source key is associated with a
#      value in the source AND the target key is NOT associated with a value,
#      the source value is copied to the target.
#
# At the bottom level, keys identify source keys, and values identify target
# keys; that is, bottom-level dicts describe the mapping of source keys to
# target keys. Target keys can be a list of keys; in this case the same value
# is copied to multiple target entries.
#
# In SAM, the transactionId is the amie_transaction_id (os:rs:ls:tid), the
# job
MAP = {
    ('SAMResponse',                   'Task'): {
        COPY_SRC_IF_SRC_SET: {
            'client':                 'client',
            'transaction_context':    'amie_packet_type',
            'transaction_id':         'amie_transaction_id',
            'job_key':                'amie_packet_id',
            'client_job_id':          'job_id',
            'task_name':              'task_name',
            'task_state':             'task_state',
            'timestamp':              'timestamp',
            'products':               'products',
            'data':                   'data',
        },
    },
    ('APacket',                       'SAMRequest'): {
        COPY_SRC_IF_SRC_SET: {
            'client':                 'client',
            'amie_packet_type':       'transaction_context',
            'amie_transaction_id':    'transaction_id',
            'amie_packet_id':         'job_key',
            'job_id':                 'client_job_id',
            'task_name':              'task_name',
            'task_state':             'task_state',
            'timestamp':              'timestamp',
            'products':               'products',
            'data':                   'data',
        },
    },
    ('APacket',                       'PeopleOrgSearchParms'): {
        COPY_SRC_IF_SRC_SET: {
            'Organization':           'name',
            'City':                   'city',
        },
    },
    ('PeopleExternalOrg',             'AMIEOrg'): {
        COPY_SRC_OR_ADD_NONE: {
            'nsfOrgCode':             'OrgCode',
        },
        COPY_SRC_IF_SRC_SET_TARG_UNSET: {
            'name':                   'Organization',
        },
        COPY_SRC_IF_SRC_SET: {
            'address':                'StreetAddress',
            'city':                   'City',
            'state':                  'State',
            'country':                'Country',
            'org_zip':                'Zip',
        },
    },
    ('SAMInstitution',                'AMIEOrg'): {
        COPY_SRC_OR_ADD_NONE: {
            'nsfOrgCode':             'OrgCode',
        },
        COPY_SRC_IF_SRC_SET_TARG_UNSET: {
            'name':                   'Organization',
            'address':                'StreetAddress',
            'city':                   'City',
            'stateProvince':          'State',
            'country':                'Country',
            'zip':                    'Zip',
        },
    },
    ('APacket',                       'choose_or_add_institution'): {
        COPY_SRC_OR_ADD_NONE: {
            'Organization':           'Organization',
            'OrgCode':                'OrgCode',
            'GrantNumber':            'GrantNumber',
        },
        COPY_SRC_OR_ADD_BLANK: {
            'Department':             'Department',
            'StreetAddress':          'StreetAddress',
            'StreetAddress2':         'StreetAddress2',
            'City':                   'City',
            'State':                  'State',
            'Country':                'Country',
            'Zip':                    'Zip',
        },
    },
    ('APacket',                       'PeoplePersonSearchParms'): {
        COPY_SRC_IF_SRC_SET: {
            'FirstName':              'firstName',
            'MiddleName':             'middleName',
            'LastName':               'lastName',
        },
    },
    ('APacket',                       'choose_or_add_person'): {
        COPY_SRC_OR_ADD_NONE: {
            'LastName':               'LastName',
            'OrgCode':                'OrgCode',
            'GrantNumber':            'GrantNumber',
        },
        COPY_SRC_OR_ADD_BLANK: {
            'FirstName':              'FirstName',
            'MiddleName':             'MiddleName',
            'Organization':           'Organization',
            'Department':             'Department',
            'Email':                  'Email',
            'BusinessPhone':          'BusinessPhone',
            'HomePhone':              'HomePhone',
            'Fax':                    'Fax',
            'RequestedLoginList':     'RequestedLoginList',
            'GlobalID':               'GlobalID',
        },
        COPY_SRC_IF_SRC_SET: {
            'PersonID':               'ACCESSUsername',
        },
    },
    ('APacket',                       'activate_person'): {
        COPY_SRC_OR_ADD_NONE: {
            'PersonID':               'PersonID',
            'GrantNumber':            'GrantNumber',
        },
        COPY_SRC_OR_ADD_BLANK: {
            'FirstName':              'FirstName',
            'MiddleName':             'MiddleName',
            'LastName':               'LastName',
            'OrgCode':                'OrgCode',
            'Organization':           'Organization',
            'Department':             'Department',
            'Email':                  'Email',
            'BusinessPhone':          'BusinessPhone',
            'HomePhone':              'HomePhone',
            'Fax':                    'Fax',
            'RequestLoginList':       'RequestLoginList',
            'GlobalID':               'GlobalID',
        },
    },
    ('APacket',                       'choose_or_add_contract'): {
        COPY_SRC_OR_ADD_NONE: {
            'GrantNumber':            'GrantNumber',
            'PfosNumber':             'PfosNumber',
            'PiLastName':             'PiLastName',
            'PiPersonID':             'PiPersonID',
            'ProjectTitle':           'ProjectTitle',
            'StartDate':              'StartDate',
            'EndDate':                'EndDate',
        },
        COPY_SRC_OR_ADD_BLANK:{
            'PiFirstName':            'PiFirstName',
        },
    },
    ('APacket',                       'choose_area_of_interest'): {
        COPY_SRC_OR_ADD_NONE: {
            'PfosNumber':             'PfosNumber',
            'ProjectTitle':           'ProjectTitle',
            'Abstract':               'Abstract',
            'PiDepartment':           'PiDepartment',
            'GrantNumber':            'GrantNumber',
        },
    },
    ('APacket',                       'choose_or_add_mnemonic_code'): {
        COPY_SRC_OR_ADD_NONE: {
            'PiOrganization':         'Institution',
            'GrantNumber':            'GrantNumber',
        },
        COPY_SRC_IF_SRC_SET: {
            'PiCity':                 'City',
            'site_org':               'UCAROrg',
        },
    },
    ('PeoplePerson',                  'AMIEPerson'): {
        COPY_SRC_IF_SRC_SET_TARG_UNSET: {
            'firstName':              'FirstName',
            'middleName':             'MiddleName',
            'lastName':               'LastName',
            'email':                  'Email',
        },
        COPY_SRC_IF_SRC_SET: {
            'username':               ['PersonID','Username','RemoteSiteLogin'],
            'active':                 'active',
            'email':                  'Email',
            'phone':                  'BusinessPhoneNumber',
            'org':                    'Organization',
        },
    },
    ('APacket',                       'create_project'): {
        COPY_SRC_OR_ADD_NONE: {
            'PiPersonID':             'PiPersonID',
            'RemoteSiteLogin':        'pi_username',
            'ProjectTitle':           'ProjectTitle',
            'project_name_base':      'mnemonic_code',
            'local_fos':              'area_of_interest',
            'GrantNumber':            'GrantNumber',
            'site_grant_key':         'contract_number',
            'BoardType':              'opportunity',
            'site_org':               'ncar_org',
            'Resource':               'requested_resource',
            'ServiceUnitsAllocated':  'requested_amount',
            'StartDate':              'StartDate',
            'EndDate':                'EndDate',
        },
        COPY_SRC_OR_ADD_BLANK:{
            'Abstract':               'Abstract',
        },
        COPY_SRC_IF_SRC_SET: {
            'RecordID':               'RecordID',
        },
    },
    ('APacket',                       'reactivate_project'): {
        COPY_SRC_OR_ADD_NONE: {
            'ProjectID':              'ProjectID',
            'Resource':               'resource_name',
        },
        COPY_SRC_OR_ADD_BLANK: {
            'AllocatedResource':      'AllocatedResource',
            'GrantNumber':            'GrantNumber',
            'StartDate':              'StartDate',
            'EndDate':                'EndDate',
            'ServiceUnitsAllocated':  'ServiceUnitsAllocated',
            'ServiceUnitsRemaining':  'ServiceUnitsRemaining',
        },
    },
    ('APacket',                       'inactivate_project'): {
        COPY_SRC_OR_ADD_NONE: {
            'ProjectID':              'ProjectID',
            'Resource':               'resource_name',
        },
        COPY_SRC_OR_ADD_BLANK: {
            'AllocatedResource':      'AllocatedResource',
            'GrantNumber':            'GrantNumber',
            'StartDate':              'StartDate',
            'EndDate':                'EndDate',
            'ServiceUnitsAllocated':  'ServiceUnitsAllocated',
            'ServiceUnitsRemaining':  'ServiceUnitsRemaining',
        },
    },
    ('APacket',                       'create_account'): {
        COPY_SRC_OR_ADD_NONE: {
            'PersonID':               'PersonID',
            'ProjectID':              'ProjectID',
            'Resource':               'requested_resource',
            'GrantNumber':            'GrantNumber',
        },
    },
    ('APacket',                       'inactivate_account'): {
        COPY_SRC_OR_ADD_NONE: {
            'PersonID':               'ACCESSUsername',
            'ProjectID':              'ProjectID',
            'Resource':               'resource_name',
        },
        COPY_SRC_OR_ADD_BLANK: {
            'Comment':                'Comment',
        },
    },
    ('APacket',                       'reactivate_account'): {
        COPY_SRC_OR_ADD_NONE: {
            'PersonID':               'ACCESSUsername',
            'ProjectID':              'ProjectID',
            'Resource':               'resource_name',
        },
        COPY_SRC_OR_ADD_BLANK: {
            'Comment':                'Comment',
        },
    },
    ('APacket',                       'renew_allocation'): {
        COPY_SRC_OR_ADD_NONE: {
            'ProjectID':              'ProjectID',
            'Resource':               'resource_name',
            'GrantNumber':            'GrantNumber',
        },
        COPY_SRC_OR_ADD_BLANK: {
            'PersonID':               'ACCESSUsername',
            'ServiceUnitsAllocated':  'requested_amount',
            'BoardType':              'opportunity',
            'site_grant_key':         'contract_number',
            'site_org':               'ncar_org',
            'local_fos':              'area_of_interest',
            'StartDate':              'StartDate',
            'EndDate':                'EndDate',
        },
        COPY_SRC_IF_SRC_SET: {
            'RecordID':               'RecordID',
            'Comment':                'Comment',
        },
    },
    ('APacket',                       'supplement_allocation'): {
        COPY_SRC_OR_ADD_NONE: {
            'PiPersonID':             'PiPersonID',
            'RemoteSiteLogin':        'pi_username',
            'ProjectTitle':           'ProjectTitle',
            'project_name_base':      'mnemonic_code',
            'local_fos':              'area_of_interest',
            'GrantNumber':            'GrantNumber',
            'site_grant_key':         'contract_number',
            'BoardType':              'opportunity',
            'site_org':               'ncar_org',
            'Resource':               'requested_resource',
            'ServiceUnitsAllocated':  'requested_amount',
            'StartDate':              'StartDate',
            'EndDate':                'EndDate',
        },
        COPY_SRC_OR_ADD_BLANK:{
            'Abstract':               'Abstract',
        },
        COPY_SRC_IF_SRC_SET: {
            'RecordID':               'RecordID',
        },
    },
    ('APacket',                       'adjust_allocation'): {
        COPY_SRC_OR_ADD_NONE: {
            'ProjectID':              'ProjectID',
            'Resource':               'resource_name',
            'ServiceUnitsAllocated':  'requested_amount',
            'GrantNumber':            'GrantNumber',
        },
        COPY_SRC_IF_SRC_SET: {
            'RecordID':               'RecordID',
            'Comment':                'Comment',
        },
    },
    ('APacket',                       'extend_allocation'): {
        COPY_SRC_OR_ADD_NONE: {
            'ProjectID':              'ProjectID',
            'Resource':               'resource_name',
            'ServiceUnitsAllocated':  'ServiceUnitsAllocated',
            'EndDate':                'EndDate',
            'GrantNumber':            'GrantNumber',
        },
        COPY_SRC_IF_SRC_SET: {
            'RecordID':               'RecordID',
            'Comment':                'Comment',
        },
    },
    ('APacket',                       'modify_user'): {
        COPY_SRC_OR_ADD_NONE: {
            'ActionType':             'ActionType',
            'PersonID':               'ACCESSUsername',
        },
        COPY_SRC_IF_SRC_SET: {
            'FirstName':              'FirstName',
            'MiddleName':             'MiddleName',
            'LastName':               'LastName',
            'OrgCode':                'OrgCode',
            'Department':             'Department',
            'Email':                  'Email',
            'BusinessPhone':          'BusinessPhone',
            'HomePhone':              'HomePhone',
            'Fax':                    'Fax',
        },
    },
    ('APacket',                       'merge_person'): {
        COPY_SRC_OR_ADD_NONE: {
            'KeepGlobalID':           'KeepGlobalID',
            'DeleteGlobalID':         'DeleteGlobalID',
            'KeepPersonID':           'KeepPersonID',
            'DeletePersonID':         'DeletePersonID',
        },
    },
    ('APacket',                       'notify_user'): {
        COPY_SRC_OR_ADD_NONE: {
            'BusinessPhoneNumber':    'BusinessPhoneNumber',
            'contingent_resources':   'AdditionalResources',
            'Email':                  'Email',
            'project_id':             'ProjectID',
            'GrantNumber':            'GrantNumber',
        },
        COPY_SRC_IF_SRC_SET: {
            'person_id':              'PersonID',
            'RemoteSiteLogin':        'RemoteSiteLogin',
            'Resource':               'Resource',
            'ResourceList':           'ResourceList',
            'resource_name':          'resource_name',
            'Username':               'Username',
        },
    },
}

def map_data(from_class, to_class, from_dict, to_dict=None):
    """Merge data from a source dict to a copy of a target dict
    
    The keys used in the source dict and their mapping to target keys is
    controlled by datamapper.MAP.
    
    :param from_class: The name of the source class (does not need to be a
        real class; see datamapper.MAP
    :type from_class: str
    :param to_class: The name of the target class (does not need to be a
        real class; see datamapper.MAP
    :type to_class: str
    :param from_dict: The source dictionary.
    :type from_dict: dict
    :param to_dict: The target dictionary.
    :type to_dict: dict
    :return: Copy of to_dict with appropriate data from from_dict
    """

    target = dict()
    submap = MAP[(from_class,to_class)]

    ap_map =  submap.get(COPY_SRC_OR_ADD_NONE,None)
    if ap_map is not None:
        _copy_all_OR_keyvals(ap_map, None, from_dict, target)

    as_map =  submap.get(COPY_SRC_OR_ADD_BLANK,None)
    if as_map is not None:
        _copy_all_OR_keyvals(as_map, '', from_dict, target)

    ss_map = submap.get(COPY_SRC_IF_SRC_SET,None)
    sstu_map = submap.get(COPY_SRC_IF_SRC_SET_TARG_UNSET,None)
    for source_key in from_dict.keys():
        source_val = from_dict[source_key]
        if source_val is None or source_val == '':
            continue

        if ss_map is not None:
            _copy_COPY_SRC_IF_SRC_SET_values(ss_map, source_key, source_val,
                                             target)

        if sstu_map is not None:
            _copy_COPY_SRC_IF_SRC_SET_TARG_UNSET_values(sstu_map, source_key,
                                                 source_val, to_dict, target)

    if to_dict is not None:
        for target_key in to_dict.keys():
            if target_key not in target:
                target[target_key] = to_dict[target_key]

    return target

def _copy_all_OR_keyvals(keymap, dflt, from_dict, target):
    for source_key in keymap.keys():
        target_key = keymap[source_key]
        source_val = from_dict.get(source_key,dflt)
        _copy_source_val_to_target(target_key, source_val, target)

def _copy_COPY_SRC_IF_SRC_SET_values(keymap, source_key, source_val, target):
    target_key = keymap.get(source_key,None)
    if target_key is None:
        return
    target[target_key] = source_val
    
def _copy_COPY_SRC_IF_SRC_SET_TARG_UNSET_values(keymap, source_key, source_val,
                                         old_target, target):
    target_key = keymap.get(source_key,None)
    if target_key is None:
        return
    target_value = None if old_target is None \
        else old_target.get(target_key,None)
    if target_value is None or target_value == '':
        target[target_key] = source_val

def _copy_source_val_to_target(tkey, source_val, target):
    if isinstance(tkey,list):
        for k in tkey:
            target[k] = source_val
    else:
        target[tkey] = source_val


