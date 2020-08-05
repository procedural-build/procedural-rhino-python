""" Python code for a task component that creates a task on the compute
server.

The task may be empty or contain a config dictionary.  If a valid config
dictionary is supplied then the task will attempt to start compute right away.
If the task is empty then a case folder will be setup on the server but no
calculation will be carried out.  You may then upload files with the "file"
component and execute the task later.

Inputs:
    operation: str   - Operation to do to the task API endpoints, options are: list|read|create|update|partial_update
    do_request: bool  - Boolean flag (from a button) to hit the API to create a new task (or update if taskId is provided)
    user: User       - A User class obtained from the login component
    files: List[str] - (optional) A list of local folders and/or files that you would like to upload before executing this task
    config: dict     - (optional) A JSON-formatted config dictionary
    task_id: str     - (optional) A taskId to get specific details of task

Output:
    out: str            - Stdout/stderr messages
    response: list|dict - The raw response data
    user: User          - The User class instance (passed through)
    task: Task          - A Task class instance that may be used for other operations on this task
"""

__author__ = "mark@procedural.build"
__version__ = "2020.04.07"

class Task():

    def __init__(self, task_id=""):
        self.task_id = task_id

    @property
    def url(self):
        _end = "%s/" % self.task_id if self.task_id else ""
        return '/api/task/%s' % _end

# Check for bad input combinations
if taskId and operation in ('list', 'create'):
    raise Exception("No taskId should be provided for list or create operations")

# Define an empty task if no config provided
if not config:
    config = {
        "task_type": "empty",
        "cmd": "empty",
        "base_dir": "task_id/foam",
        "cpus": [1, 1, 1]
    }

# Get the response data
_task = Task(task_id=taskId)
method = user.operation_method(operation)
if do_request:
    response = user.request(method, _task.url, data={'config': config})
else:
    response = user.get_cached_response(method, _task.url)
    if response:
        print("Using cached response")

# If we have response data then output it here
if response:
    if type(response) == list:
        print("Task ids:")
        uids = [i.get('uid') for i in response]
        for i in uids:
            print(i)
    else:
        print("Task details:")
        print(response)
        if type(response) == dict:
            taskId = response.get('uid', None)
            if taskId:
                task = Task(task_id=taskId)
            response = [response]
