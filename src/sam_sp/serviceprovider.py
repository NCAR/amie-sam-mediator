import sys, json
import logging
from logdumper import LogDumper
from misctypes import DateTime
from serviceprovider import ServiceProviderIF
from taskstatus import TaskStatus
from person import AMIEPerson
from organization import AMIEOrg
from person import AMIEPerson
from sam_sp.peopleclient import PeopleClient
from sam_sp.peopledata import PeopleExternalOrg
from sam_sp.samclient import SAMClient
from sam_sp.datamapper import map_data
from sam_sp.task import TaskService
from sam_sp.mnemonic import MnemonicCodeMaker

class ServiceProvider(ServiceProviderIF):
    """SAM implementation of a ServiceProvider

    Refer to mediator.serviceprovider for API documentation

    Note that the SAM serviceprovider maintains a local cache of "tasks" (see
    task.TaskService). This task data is refreshed when get_tasks() is run.
    When a serviceprovider method is expected to submit a request to SAM and
    returns a TaskStatus object (e.g. choose_or_add_org()), it first checks to
    see if the task was previously submitted by querying the cache (via the
    TaskService's lookup_task() method); if the task was previously submitted,
    the method returns the status of the cached task without contacting SAM.

    """

    def __init__(self, *args, **kwargs):
        super(ServiceProvider,self).__init__(*args, **kwargs)
        self.logger = logging.getLogger("sp.sam")
        self.logdumper = LogDumper(self.logger)
        self.active_tasks = None
    
    def apply_config(self, config):
        self.people_client = PeopleClient(
            config['people_url'],
            config['people_user'],
            config['people_password'],
            self.logger
        )
        self.mnemonic_code_maker = MnemonicCodeMaker(
            int(config['sam_mnem_code_suggestions_min']),
            int(config['sam_mnem_code_suggestions_max'])
        )
        self.sam_client = SAMClient(
            config['sam_url'],
            config['sam_user'],
            config['sam_password'],
            int(config['pause_max']),
            self.people_client,
            self.mnemonic_code_maker
        )
        self.task_service = TaskService(self.sam_client,self.people_client)

    def get_local_task_name(self, method_name, *args, **kwargs) -> str:
        if method_name == "choose_or_add_grant":
            return "choose_or_add_contract"
        elif method_name == "choose_or_add_local_fos":
            return "choose_area_of_interest"
        elif method_name == "choose_or_add_project_name_base":
            return "choose_or_add_mnemonic_code"
        elif method_name == "update_allocation":
            allocationType = kwargs['AllocationType']
            if allocationType == "renewal":
                task_name = "renew_allocation"
            elif allocationType == "supplement":
                task_name = "supplement_allocation"
            elif allocationType == "adjustment":
                task_name = "adjust_allocation"
            elif allocationType == "extension":
                task_name = "extend_allocation"
#           elif allocationType == "transfer":
#               task_name = "transfer_allocation"
#           elif allocationType == "advance":
#               task_name = "advance_allocation"
            else:
                task_name = None
            return task_name
        return method_name
        
    def get_tasks(self, active=True, wait=None, since=None) -> list:
        tasks = self.task_service.get_tasks(active, wait, since)
        return self._convert_task_dicts_to_TaskStatus_list(tasks)

    def _convert_task_dicts_to_TaskStatus_list(self, tasks):
        ts_list = list()
        for task in tasks:
            ts_list.append(TaskStatus(task))
        return ts_list

    def _lookup_task(self, task_name, kwargs):
        return self.task_service.lookup_task_status(task_name, kwargs)
    
    def _submit_request(self, reqname, parmdict, choices=None):
        return self.task_service.submit_request(reqname, parmdict,
                                                choices=choices)
    
    def clear_transaction(self, amie_transaction_id):
        self.sam_client.put("transactions/AMIE/"+amie_transaction_id+"/state/cleared",'')
        # clear

    def lookup_org(self, *args, **kwargs) -> AMIEOrg:
        orgCode = kwargs.get('OrgCode',None)

        self.logdumper.debug("Looking up orgCode="+orgCode)
        result = self.sam_client.get("institution/"+orgCode+"?idtype=NSFOrgCode")
        if not result:
            self.logdumper.debug("  org not found")
            return None
        self.logdumper.debug("get organizations/<orgcode> result:",result)
        org_parms = map_data('SAMInstitution','AMIEOrg',result,kwargs)
        
        self.logdumper.debug("supplemented org_parms",org_parms)
        return AMIEOrg(**org_parms)

    def choose_or_add_org(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('choose_or_add_institution', kwargs)
        if ts:
            self.logger.debug("choose_or_add_org: ts=",ts)
            return ts
        choice_parms = map_data('APacket','PeopleOrgSearchParms',kwargs)
        orgs = self.people_client.fuzzymatch_org(**choice_parms)
        orgCode = kwargs['OrgCode']
        # Note fuzzymatch_org will initialize org cache
        org = self.people_client.get_cached_org_by_nsf_code(orgCode)
        products = dict()
        if org:
            # PeopleDB has nsf code but not SAM. Initialize state to 'syncing'
            init_state='syncing'
            products['external_org_id'] = orgCode
        return self._submit_request('choose_or_add_institution',
                                    kwargs, orgs, **products)

    def lookup_person(self, *args, **kwargs) -> AMIEPerson:
        username = kwargs.get('PersonID',None)
        result = None
        if username:
            result = self.sam_client.get("person/"+username)
        if not result:
            id = kwargs.get('GlobalID',None)
            if id:
                result = self.sam_client.get("person/"+id+"?idtype=accessglobalid")
        if result:
            return AMIEPerson(result)
        return None

    def choose_or_add_person(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('choose_or_add_person', kwargs)
        if ts:
            return ts
        choice_parms = map_data('APacket','PeoplePersonSearchParms',kwargs);
        persons = self.people_client.fuzzymatch_person(**choice_parms)
        return self._submit_request('choose_or_add_person',
                                    kwargs, persons)

    def update_person_DNs(self, *args, **kwargs) -> TaskStatus:
        kwargs['task_state'] = "successful"
        ts = TaskStatus(*args, **kwargs)
        return ts

    def activate_person(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('activate_person', kwargs)
        if ts:
            return ts
        return self.task_service.submit_request('activate_person',kwargs)


    def lookup_grant(self, *args, **kwargs) -> str:
        grantNumber = kwargs['GrantNumber']
        result = self.sam_client.get("grant/"+grantNumber)
        if not result:
            return None
        return result['site_grant_key']
    
    def choose_or_add_grant(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('choose_or_add_contract', kwargs)
        if ts:
            return ts
        grantNumber = kwargs['GrantNumber']
        grants = self.sam_client.get("grants/"+grantNumber)
        grant_choices = self._build_contract_choices(grants)
        return self._submit_request('choose_or_add_contract',
                                    kwargs, grant_choices)

    def _build_contract_choices(self, grants):
        gchoices = [['ContractNumber','Title','PI','StartDate','EndDate']]
        for grant in grants:
            gchoice = [
                grant['contractNumber'],
                grant['title'],
                grant['PI'],
                grant['startDate'],
                grant['endDate']
                ]
            gchoices.append(gchoice)
        return gchoices
        
    def lookup_local_fos(self, *args, **kwargs) -> str:
        fosNumber = kwargs['PfosNumber']
        aoi = self.sam_client.get("fosaoi/"+fosNumber)
        if aoi['aoi'] == "Other":
            return None
        return aoi['aoi']
    
    def choose_or_add_local_fos(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('choose_area_of_interest', kwargs)
        if ts:
            return ts
        aois = self._build_aoi_choices()
        return self._submit_request('choose_area_of_interest', kwargs, aois)
        
    def _build_aoi_choices(self):
        aoi_recs = self.sam_client.get("aois")
        choices = [["AreaOfInterest","Group"],["Other","Other"]]
        aois = []
        for aoi_rec in aoi_recs:
            if aoi_rec['areaOfInterest'] != "Other":
                aois.append([aoi_rec['areaOfInterest'],aoi_rec['group']])
        sorted_aois = sorted(aois,key=lambda s: s[0])
        for aoi in aois:
            choices.append(aoi)
        return choices
        

    def lookup_project_name_base(self, *args, **kwargs) -> str:
        # The people_client load_internal_orgs() and load_external_orgs()
        # functions will populate local caches used by get_cached_internal_org()
        # and get_cached_org_by_nsf_code(), respectively. The sam_client
        # load_mnemonic_codes() will populate a local cache used by
        # get_mnemonic_code_by_description(); call the load*() functions to
        # make sure the caches have the latest data. Note that this function
        # is always called before choose_or_add_project_name_base(), so the
        # latter can rely on caches being current.
        self.people_client.load_internal_orgs()
        self.people_client.load_external_orgs()
        self.sam_client.load_mnemonic_codes()

        site_org = kwargs.get('site_org',None)
        org_code = kwargs.get('PiOrgCode',None)
        # The PI can have both an internal and external org; if they have both,
        # the external org is an upper-level internal org that has an external
        # org entry. If both site_org and org_code are not None, we want
        # to return None because we don't know which org to use for the
        # mnemonic code; we will let choose_or_add_project_name_base() resolve
        # the mnemonic code.
        if site_org and org_code:
            return None

        if site_org:
            return self.sam_client.get_mnemonic_code_for_org(site_org)
        elif org_code:
            return self.sam_client.get_mnemonic_code_for_inst(org_code)
        else:
            raise ServiceProviderRequestFailed("Unable to determine" +\
                                               " PI institution/organization")

    def choose_or_add_project_name_base(self, *args, **kwargs) -> TaskStatus:
        # See comments at start of lookup_project_name_base(). We will assume
        # that lookup_project_name_base will always be called before
        # choose_or_add_project_name_base(), so the mnemonic codes cache should
        # be up-to-date
        site_org = kwargs.get('site_org',None)
        org_code = kwargs.get('PiOrgCode',None)
        choices = self.sam_client.build_mnemonic_code_choices(site_org,
                                                              org_code)
        return self._submit_request('choose_or_add_mnemonic_code',
                                    kwargs, choices)
        
    def create_project(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('create_project', kwargs)
        if ts:
            return ts
        return self._submit_request('create_project',kwargs)
        
    def lookup_project(self, *args, **kwargs) -> TaskStatus:
        recordID = kwargs.get("RecordID",None)
        if recordID is None:
            return None
        
        self.logdumper.debug("Looking up RPC task for RecordID="+recordID)
        ts = self.sam_client.get("task/AMIE/"+recordID+"/create_project")
        return ts

    def reactivate_project(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('reactivate_project', kwargs)
        if ts:
            return ts
        return self._submit_request('reactivate_project',kwargs)

    def inactivate_project(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('inactivate_project', kwargs)
        if ts:
            return ts
        return self._submit_request('inactivate_project',kwargs)

    def create_account(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('create_account', kwargs)
        if ts:
            return ts
        failed_ts = self._verify_ProjectID_for_op('create_account', kwargs)
        if failed_ts:
            return failed_ts

        return self._submit_request('create_account',kwargs)

    def inactivate_account(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('inactivate_account', kwargs)
        if ts:
            return ts
        failed_ts = self._verify_ProjectID_for_op('inactivate_account', kwargs)
        if failed_ts:
            return failed_ts

        return self._submit_request('inactivate_account',kwargs)

    def reactivate_account(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('reactivate_account', kwargs)
        if ts:
            return ts
        failed_ts = self._verify_ProjectID_for_op('reactivate_account', kwargs)
        if failed_ts:
            return failed_ts

        return self._submit_request('reactivate_account',kwargs)

    def update_allocation(self, *args, **kwargs) -> TaskStatus:
        allocationType = kwargs['AllocationType']
        task_name = None
        # WORK HERE
        if allocationType == "renewal":
            task_name = "renew_allocation"
        elif allocationType == "supplement":
            task_name = "supplement_allocation"
        elif allocationType == "adjustment":
            task_name = "adjust_allocation"
        elif allocationType == "extension":
            task_name = "extend_allocation"
#       elif allocationType == "transfer":
#           task_name = "transfer_allocation"
#       elif allocationType == "advance":
#           task_name = "advance_allocation"
        else:
            return self.task_service.create_failed_TaskStatus(
                'update_allocation', kwargs,
                "Unsupported AllocationType: " + allocationType)

        ts = self._lookup_task(task_name, kwargs)
        if ts:
            return ts
        failed_ts = self._verify_ProjectID_for_op(task_name, kwargs)
        if failed_ts:
            return failed_ts

        return self._submit_request(task_name, kwargs)

    def _verify_ProjectID_for_op(self, op, kwargs):
        project_id = kwargs.get("ProjectID",None)
        if not project_id:
            return self.task_service.create_failed_TaskStatus(op, kwargs,
                "NCAR requires ProjectID for '" + op + "' operation")

        return None

    def modify_user(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('modify_user', kwargs)
        if ts:
            return ts
        return self._submit_request('modify_user',kwargs)


    def merge_person(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('merge_person', kwargs)
        if ts:
            return ts
        return self._submit_request('merge_person',kwargs)


    def notify_user(self, *args, **kwargs) -> TaskStatus:
        ts = self._lookup_task('notify_user', kwargs)
        if ts:
            return ts
        return self._submit_request('notify_user',kwargs)
        
