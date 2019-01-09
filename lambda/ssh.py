# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend as crypto_default_backend
import paramiko
import io
import boto3
import json

class InvalidParameterError(Exception):
    def __init__(self, message):
        self.message = message

class SSHCommandError(Exception):
    def __init__(self, ip, nested_exception):
        self.nested_exception = nested_exception
        self.ip = ip


def generate_key_pair(comment):
    key = rsa.generate_private_key(
            backend=crypto_default_backend(),
            public_exponent=65537,
            key_size=2048
            )
    private_key = key.private_bytes(
            crypto_serialization.Encoding.PEM,
            crypto_serialization.PrivateFormat.TraditionalOpenSSL,
            crypto_serialization.NoEncryption())
    public_key = key.public_key().public_bytes(
            crypto_serialization.Encoding.OpenSSH,
            crypto_serialization.PublicFormat.OpenSSH
            )

    private_key_str = private_key.decode('utf-8')
    public_key_str = public_key.decode('utf-8') + " " + comment

    return [private_key_str, public_key_str]

def run_command(ip_addresses, username, private_key, command):
    private_key_str = io.StringIO()
    private_key_str.write(private_key)
    private_key_str.seek(0)

    key = paramiko.RSAKey.from_private_key(private_key_str)

    client = paramiko.client.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # connect and execute the command
    for ip in ip_addresses:
        try:
            print("SSH: Connecting to %s as user %s." % (ip, username))
            client.connect(ip, 
                    username = username,
                    pkey = key,
                    look_for_keys = False)
            stdin, stdout, stderr = client.exec_command(command)
            print("SSH: Successfully executed command '%s' on %s as user %s." % (command, ip, username))
        finally:
            client.close()
