""" Python code for a task component that uploads files for

The task may be empty or contain a config dictionary.  If a valid config
dictionary is supplied then the task will attempt to start compute right away.
If the task is empty then a case folder will be setup and the

Inputs:
    operation:           - Operation to perform (list, update)
    user: User           - An instance of the User class from the `login` component
    taskId: srt          - The uid of the task to upload files to
    files: List[str]     - A list of local folders and/or files that you would like to upload before executing this task

Output:
    out: str             - Stdout/stderr messages
    user: User           - The User class instance (passed through)
    task: Task           - The Task class instance (passed through)
"""

__author__ = "mark@procedural.build"
__version__ = "2020.04.07"

import os

# Cast the files to a list
files = files or []
target_path = target_path or "foam"

if not taskId:
    raise Exception("taskId is required")

# Check that the files/paths exist and expand folders to a list of all files within
_files = []
for path in files:
    if not os.path.exists(path):
        raise Exception("Path %s not found" % (path))

    if os.path.isdir(path):
        print("Found directory at %s" % path)
        for root, dirs, files in os.walk(path):
            print(root, dirs, files)
            for file in files:
                _files.append(os.path.join(root, file))
    else:
        _files.append(path)

# Upload the files to the server
responses = []
for file in _files:
    destination_path = os.path.join(target_path, file.replace(os.path.split(path)[0], "")[1:])
    print(destination_path)
    url = "/api/task/%s/file/%s/" % (taskId, destination_path)
    with open(file, 'rb') as local_file:
        data = local_file.read()
        if do_upload:
            response = user.request('PUT', url, data=data, sendRaw=True)
        else:
            response = user.get_cached_response('PUT', url)
        # append to the list of responses
        responses.append(response)




"""
for file in files:
    with open(file, 'rb') as f:
        data = f.read()
        newObj = user.request('PUT', docObjUrl, data=data,
            extra_headers={ 'Content-Disposition': 'attachment; filename=%s.json'%(uid)},
            sendRaw=True
        )
"""
