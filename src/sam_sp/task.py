import json
import logging
from misctypes import TimeUtil
from miscfuncs import to_expanded_string
from logdumper import LogDumper
from taskstatus import TaskStatus,Product
from sam_sp.samclient import SAMClient
from sam_sp.peopleclient import PeopleClient
from sam_sp.datamapper import map_data


class SAMRequestBody(dict):
    timeutil = TimeUtil()

    def __init__(self, task_name, packet_dict):
        request_body = map_data('APacket', 'SAMRequest', packet_dict)
        request_body['client'] = 'AMIE'
        request_body['task_name'] = task_name
        request_body['task_state'] = 'nascent'
        request_body['timestamp'] = int(SAMRequestBody.timeutil.timestamp()*1000)
        dict.__init__(self, **request_body)

    @staticmethod
    def create(task_name, packet_dict, choices=None, **kwargs):
        request_body = SAMRequestBody(task_name, packet_dict)
        products = []
        for key, value in kwargs.items():
            products.append(Product(key,value))
        request_body['products'] = products
        print("DEBUG SAMRequestBody.create task_name="+task_name+" packet_dict="+to_expanded_string(packet_dict))
        parameters = map_data('APacket', task_name,
                              SAMRequestBody._flatten_dict(packet_dict))
        print("DEBUG after mapping parameters="+to_expanded_string(parameters))

        data = dict()
        data['parameters'] = parameters
        if choices:
            data['choices'] = choices
        request_body['data'] = data
        return request_body

    @staticmethod
    def _flatten_dict(packet_dict):
        flat_dict = dict()
        for key in packet_dict:
            value = packet_dict[key]
            if (value is None) or isinstance(value,str):
                flat_dict[key] = value
            else:
                flat_dict[key] = json.dumps(value)
            
        return flat_dict

class SAMTask(object):
    timeutil = TimeUtil()

    def __init__(self, task_data):
        self.key = SAMTask.get_key(task_data)
        self.state = task_data['task_state']
        ts = task_data['timestamp']
        self.timestamp = SAMTask.timeutil.timestamp_to_isoformat(ts/1000)
        self.task = task_data
        self.task_status = None
        
    def __str__(self):
        return self.key + '(' + self.state + ')@' + self.timestamp

    @staticmethod
    def get_key(task_data, task_name=None):
        tid = task_data['amie_transaction_id']
        jkey = task_data['amie_packet_id']
        name = task_name if task_name else task_data['task_name']
        return tid + '/' + jkey + '/' + name

class SAMTaskCache(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self,**kwargs)


    def update(self, task_data) -> SAMTask:
        # argument can be SAMTask or task dict
        if isinstance(task_data, dict):
            task = SAMTask(task_data)
        else:
            task = task_or_list

        key = task.key
        state = task.state
        if state == 'cleared':
            if key in self.keys():
                del self[key]
        else:
            self[key] = task

        return task

    def lookup(self, task_data, task_name=None):
        # argument can be SAMTask or task dict
        if isinstance(task_data, dict):
            key = SAMTask.get_key(task_data, task_name)
        else:
            key = task.key
            
        return self.get(key, None)

class TaskService(object):

    def __init__(self, sam_client, people_client):
        """Manager for "tasks" processed by the SAM service provider

        :param sam_client: SAM client
        :type sam_client: SAMClient
        :param people_client: PeopleSearch client
        :type people_client: PeopleClient
        """

        self.sam_client = sam_client
        self.people_client = people_client
        self.logger = logging.getLogger("sp.sam")
        self.logdumper = LogDumper(self.logger)
        self.timeutil = TimeUtil()
        self.task_cache = SAMTaskCache()

    def lookup_task_status(self, task_name, packet_dict):
        st = self.task_cache.lookup(packet_dict, task_name)
        if st is None:
            return None
        if st.task_status is None:
            st.task_status = TaskStatus(st.task)
        return st.task_status
        
    def submit_request(self, task_name, packet_dict,
                       choices=None) -> TaskStatus:
        """Submit (POST) a new task to SAM or revisit (PUT) an existing task

        :param task_name: The name of the new task
        :type task_name: str
        :param packet_dict: ActionablePacket data
        :type packet_dict: dict
        :param choices: If given, a list of choices
        :type choices: list or None
        :return: TaskStatus
        """
        
        request = SAMRequestBody.create(task_name, packet_dict, choices)
        jsrequest = json.dumps(request)

        self.logdumper.debug("Submitting POST request to SAM:",request)
        self.logger.debug("  request JSON:\n   "+jsrequest)

        result = self.sam_client.post('tasks',json.dumps(request))
    
        self.logdumper.debug("POST result:",result)

        task = self.get_TaskStatus_from_result(result)
        return task

    def get_TaskStatus_from_result(self, result):
        task = self._convert_result(result)
        st = self.task_cache.update(task)
        self.logger.debug("get_TaskStatus_from_result: %",st)

        return TaskStatus(task)

    def create_failed_TaskStatus(self, task_name, packet_dict, msg):
        task = dict(packet_dict)
        task['client'] = 'AMIE'
        task['task_name'] = task_name
        task['task_state'] = 'nascent'
        task['timestamp'] = int(self.timeutil.timestamp()*1000)
        ts = TaskStatus(task)
        ts.fail(msg)
        task['products'] = ts['products']
        return ts
        
    def get_tasks(self, active=True, wait=None, since=None) -> list:
        """Get tasks list from SAM

        Query SAM for tasks. If a task's state is 'delegated', send a request
        to PeopleDB and update the task's state in SAM to 'syncing' if the
        request is successful. If a task's state is 'syncing', revisit the
        task to check if the sync has completed.

        :param active: if True, restrict query to active states
        :type active: bool
        :param wait: if given, max seconds to wait for a response
        :type wait: int
        :param since: if given, restrict to tasks modified since given time
        :type since: DateTime
        :return: list of task dicts
        """

        start_time = self.timeutil.now();
        
        # SAM will return immediately if there are any tasks that have been
        # updated after "since"; wait is only used if there is nothing to
        # return. But see _handle_internal_tasks()
        tasks = self._get_tasks_from_SAM(active=active, wait=wait, since=since)

        self.logger.debug("get_tasks:")

        for task in tasks:
            st = self.task_cache.update(task)
            self.logger.debug("  %s",st)

        updated_tasks = self._process_cached_tasks(start_time, wait, since)
        return updated_tasks

    def _get_tasks_from_SAM(self, active, wait, since) -> list:
        parms  = []
        if active:
            parms.append("active=true")
        if wait:
            parms.append("maxWaitSecs="+str(wait))
        if since:
            parms.append("since="+str(int(since)))
        parmstr = ("?" + "&".join(parms)) if parms else ""

        rel_url = "tasks/AMIE"+parmstr
        self.logdumper.debug("get_tasks: SAM GET "+rel_url)
        results = self.sam_client.get(rel_url)
        if isinstance(results,list):
            self.logdumper.debug("get_tasks: got "+str(len(results))+" records")
        else:
            self.logdumper.debug("get_tasks: got non-list (?)",results)

        tasks = self._convert_results(*results)
        return tasks

    def _convert_results(self, *results):
        converted_results = []
        for result in results:
            converted_result = self._convert_result(result)
            if converted_result['task_state'] == 'cleared':
                continue
            converted_results.append(converted_result)
        converted_results.sort(key=lambda t: t['timestamp'])
        return converted_results

    def _convert_result(self, result, request=None):
        converted_result = map_data('SAMResponse','Task',result, request)
        state = converted_result['task_state']
        if state == "rejected":
            converted_result['task_state'] = 'in-progress'
        return converted_result

    def _process_cached_tasks(self, start_time, wait, since):

        cached_tasks = list(self.task_cache.values())
        cached_tasks.sort(key=lambda t: t.timestamp)

        delegated_tasks = self._get_cached_tasks_for_state('delegated')
        self._delegate_tasks(delegated_tasks)

        syncing_tasks = self._get_cached_tasks_for_state('syncing')

        if syncing_tasks:
            self._revisit_tasks(syncing_tasks)

        cached_tasks = list(self.task_cache.values())
        cached_tasks.sort(key=lambda t: t.timestamp)

        if since is None:
            iso_since = ""
        else:
            iso_since = self.timeutil.timestamp_to_isoformat(since/1000)

        updated_tasks = list()
        for st in cached_tasks:
            if st.timestamp > iso_since:
                updated_tasks.append(st.task)

        return updated_tasks

    def _get_cached_tasks_for_state(self, target_state):
        tasks = list()
        for st in self.task_cache.values():
            state = st.state
            if state == target_state:
                tasks.append(st.task)
        return tasks
   
    def _delegate_tasks(self, delegated_tasks):
        if delegated_tasks:
            self.logger.debug("_delegate_tasks:")
            for task in delegated_tasks:
                self._delegate_task(task)
        
    def _delegate_task(self, task):
        start_st = self.task_cache.lookup(task)
        taskname = task['task_name']
        if taskname == "choose_or_add_institution":
            updated_task = self._choose_or_add_institution(task)
        else:
            updated_task = self._change_SAM_task_state_to_syncing(task)
        
        st = self.task_cache.update(updated_task)
        self.logger.debug("  %s -> %s", start_st, st)

    def _choose_or_add_institution(self, task):
        task['timestamp'] = self.timeutil.timestamp()*1000

        ts = TaskStatus(task)
        org_id = ts.get_product_value('external_org_id')
        data = task['data']
        parameters = data['parameters']
        nsf_org_code = parameters['OrgCode']
        self.logdumper.debug("PEOPLE set_nsf_code_for_external_org: org_id=" +\
                             org_id + " nsf_org_code=" + nsf_org_code)
        result = self.people_client.set_nsf_code_for_external_org(org_id,
                                                                  nsf_org_code)
        self.logdumper.debug("PEOPLE result:",result)
        if 'nsfOrgCode' not in result or nsf_org_code != result['nsfOrgCode']:
            raise RuntimeError("Unable to set nsf_org_code in PeopleDB: " + \
                               "result:\n" + to_expanded_string(result))
        return self._change_SAM_task_state_to_syncing(task)

    def _change_SAM_task_state_to_syncing(self, task):
        task_key = SAMTask.get_key(task)
        url = 'tasks/AMIE/' + task_key + '/state'
        data = '"syncing"'
        result = self.sam_client.put(url,data)
        updated_task = self._convert_result(result, task)
        return updated_task

    def _calculate_remaining_time(self, start_time, wait):
        if not wait:
            return 0
        curr_time = self.timeutil.now();
        elapsed_time = curr_time - start_time
        elapsed_secs = int(elapsed_time.total_seconds() + 0.5)
        if elapsed_secs < wait:
            return wait - elapsed_secs
        return 0

    def _revisit_tasks(self, tasks):
        self.logger.debug("_revisit_tasks:")

        for task in tasks:
            self._revisit_task(task)
    
    def _revisit_task(self, task):
        start_st = self.task_cache.lookup(task)

        task_key = SAMTask.get_key(task)
        url = 'tasks/AMIE/' + task_key
        request = map_data('APacket','SAMRequest', task)
        request['client'] = 'AMIE'

        self.logdumper.debug("Submitting PUT request to SAM, url=" + url + ":",
                             request)

        result = self.sam_client.put(url,json.dumps(request))
    
        self.logdumper.debug("PUT result:",result)

        updated_task = self._convert_result(result, task)
        st = self.task_cache.update(updated_task)
        self.logger.debug("  %s -> %s", start_st, st)
        return
        
    
