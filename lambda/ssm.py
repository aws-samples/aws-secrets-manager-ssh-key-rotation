# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import boto3
import time
import datetime

# Loop until less than this time is remaining
MIN_REMAINING_TIME = 20*1000 # 20 seconds

# Time to sleep between calls to get command status
SLEEP_TIME = 5 # 5 seconds

# How far back in hours should we look for the Add Key SSM Command Invocation
SEARCH_WINDOW_HOURS = 4 # hours

class CommandError(Exception):
    def __init__(self, status, status_details):
        self.status = status
        self.status_details = status_details

class SSM:
    def __init__(self, context, targets, username):
        self.client = boto3.client('ssm')
        self.context = context
        self.targets = targets
        self.username = username

    def send_command(self, commands, action, version):
        return self.client.send_command(Targets = self.targets,
            DocumentName = "AWS-RunShellScript",
            Comment = f"{action} {version}",
            Parameters = {
                'commands' : commands,
            }
        )

    def add_public_key(self, public_key, new_version):
        commands = [
                f"key_file=~{self.username}/.ssh/authorized_keys",
                f"COUNT=`grep -c \"{new_version}\" $key_file`",
                f"if [ $COUNT -eq 0 ]",
                f"  then",
                f"    echo \"Adding public key with comment {new_version} to authorized_keys file for {self.username}\" ",
                f"    echo \"{public_key}\" >> $key_file",
                f"  else",
                f"    echo \"Public key with comment {new_version} already exists\"",
                f"fi"
                ]
        response = self.send_command(commands,'add_key', new_version)
        return response['Command']['CommandId']

    def del_public_key(self, previous_version):
        commands = [
                f"key_file=~{self.username}/.ssh/authorized_keys",
                f"echo \"Removing public key with comment {previous_version} from authorized_keys file for {self.username}, original file is stored with .bak extension\" ",
                f"sed -i'.bak' \"/{previous_version}/d\" $key_file",
                ]
        response = self.send_command(commands, 'delete_key', previous_version)
        return response['Command']['CommandId']

    def wait_completion(self, command_id):
        while(True):
            response = self.client.list_commands(CommandId=command_id)
            cmd = response['Commands'][0]

            status = cmd['Status']

            if status in ['Pending', 'InProgress']:
                if(self.context.get_remaining_time_in_millis() > MIN_REMAINING_TIME):
                    time.sleep(SLEEP_TIME)
                else:
                    raise CommandError('Timeout', 'Timed out waiting for completion')
            elif status in ['Success']:
                return True
            else:
                raise CommandError(status, cmd['StatusDetails'])


    def get_private_ips(self, instance_ids):
        if(len(instance_ids) == 0):
            return []

        private_ips = []

        ec2 = boto3.client('ec2')
        paginator = ec2.get_paginator('describe_instances')
        filters = [{
            "Name" : "instance-id",
                "Values" : instance_ids
        }]

        page_iter = paginator.paginate(Filters = filters)
        for page in page_iter:
            for r in page['Reservations']:
                for i in r['Instances']:
                    if(len(i['NetworkInterfaces']) != 0):
                        # pluck the primary private IP address of the first ENI
                        ip = i['NetworkInterfaces'][0]['PrivateIpAddress']
                        private_ips.append(ip)
        return private_ips

    def get_addrs_for_add_key(self, new_version):
        instance_ids = []
        paginator = self.client.get_paginator('list_commands')

        now = datetime.datetime.now()
        delta = datetime.timedelta(hours=SEARCH_WINDOW_HOURS)
        search_start = now - delta
        search_start_iso = search_start.replace(microsecond=0).isoformat() + 'Z'

        search_comment = f"add_key {new_version}"
        # Find the SSM Run Command Invocation for the add_key:
        # Look for Command Invocations that were executed at most 4 hours ago
        # AND have a comment 'add_key {new_version}'
        # AND have status Success
        # => return the Private IP addresses for Instance IDs in this command
        command_id = None
        page_iter = paginator.paginate(Filters = [{
                'key' : 'InvokedAfter',
                'value' : search_start_iso
            }])
        for page in page_iter:
            for c in page['Commands']:
                if('Comment' in c):
                    comment = c['Comment']
                    if(comment == search_comment and c['Status'] == 'Success'):
                        command_id = c['CommandId']
                        break

        if(command_id == None):
            # Could not find a Successful command, flag an error
            raise CommandError('Run Command not found',
                    f"Could not find Successful Run Command with comment 'add_key {new_version}'")

        paginator = self.client.get_paginator('list_command_invocations')
        page_iter = paginator.paginate(CommandId = command_id)
        for page in page_iter:
            for c in page['CommandInvocations']:
                instance_ids.append(c['InstanceId'])

        ip_addresses = self.get_private_ips(instance_ids)
        return ip_addresses
