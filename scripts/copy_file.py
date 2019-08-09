# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import paramiko
import io
import sys
import boto3
import json
from botocore.exceptions import ClientError


def get_private_key():
    secret_name = "/dev/ssh"
    client = boto3.client('secretsmanager', region_name='us-east-1')

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    else:
        secret = get_secret_value_response['SecretString']
            
        secret_dict = json.loads(secret)
        private_key = secret_dict['PrivateKey']
        
        return private_key

def copy_file(private_key, user, ip, local_path, remote_path):
    private_key_str = io.StringIO()
    private_key_str.write(private_key)
    private_key_str.seek(0)

    key = paramiko.RSAKey.from_private_key(private_key_str)

    private_key_str.close()
    del private_key_str

    trans = paramiko.Transport(ip, 22)
    trans.start_client()
    trans.auth_publickey(user, key)

    del key

    print('Opening transport')
    conn = trans.open_session()

    print('Opening SFTP session')
    sftp = paramiko.SFTPClient.from_transport(trans)

    print('Copying local path {} to remote path {}'.format(local_path, remote_path))
    sftp.put(local_path, remote_path) 

    print('Closing SFTP session')
    sftp.close()

    print('Closing transport')
    trans.close()

private_key = get_private_key()
copy_file(private_key, sys.argv[1], sys.argv[2], 'testfile.txt', 'testfile.txt')

# Overwrite and delete the private_key variable, just for safety
private_key = '##############################################'
del private_key
