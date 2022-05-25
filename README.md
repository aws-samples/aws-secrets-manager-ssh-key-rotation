## AWS Secrets Manager Ssh Key Rotation

### Secrets Manager - Lambda rotation function for SSH Keys.
Please see a walk-through of using this function in [How to use AWS Secrets Manager to securely store and rotate SSH key pairs](https://aws.amazon.com/blogs/security/how-to-use-aws-secrets-manager-securely-store-rotate-ssh-key-pairs/).

The above post shows you how to deploy the rotation Lambda function and resources to test the rotation in the ``us-east-1`` AWS region. See below if you want to deploy the function to a different region, or want to re-build the Lambda function ZIP.

## License Summary

This sample code is made available under a modified MIT license. See the LICENSE file.


## Deploying to an AWS region other than ``us-east-1``
To deploy the rotation Lambda function to an AWS Region other than ``us-east-1``:

1. Clone this repository to your desktop using git.
```
git clone https://github.com/aws-samples/aws-secrets-manager-ssh-key-rotation.git
```
1. Create a new S3 bucket or reuse an existing S3 bucket in your chosen AWS region where you want to deploy the Lambda function. This S3 bucket will store the Lambda function ZIP file.
1. Upload the packaged Lambda function ZIP file (dist/rotate_ssh_python3.9.zip)[dist/rotate_ssh_python3.9.zip] to your S3 bucket. Note the S3 URL to the uploaded ZIP file (e.g. ``s3://bucketname/path/to/rotate_ssh_python3.9.zip``)
1. Edit the *packaged* CloudFormation template (secretsmanager_rotate_ssh_keys_packaged.yaml)[secretsmanager_rotate_ssh_keys_packaged.yaml] and change the ``CodeUri`` to point to your S3 URL. I.e. change this line in the file ``secretsmanager_rotate_ssh_keys_packaged.yaml``:
```
      CodeUri: s3://awsiammedia/public/sample/SecretsManagerStoreRotateSSHKeyPairs/rotate_ssh.zip
```
1. Now you can (create a new Stack in CloudFormation)[https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-console-create-stack.html] in your chosen AWS region using the modified *packaged* template.

## Deploying the Lambda function ZIP file after making code changes
The Lambda rotation function uses the Python (``paramiko``)[https://www.paramiko.org/] package that requires natively compiled cryptography libraries. For this reason, the Lambda function must be packaged on the same environment and architecture as the (Lambda run-time for Python 3.9)[https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html] - Amazon Linux 2 on x86_64.

The Lambda function is deployed using an (AWS Serverless Application Model (SAM)_[https://aws.amazon.com/serverless/sam/] template (``secretsmanager_rotate_ssh_keys.template``)[secretsmanager_rotate_ssh_keys.template] that must be (packaged)[https://docs.aws.amazon.com/cli/latest/reference/cloudformation/package.html] before it can be deployed.

To deploy the Lambda function ZIP file after making code changes, or to re-package the CloudFormation template:

1. Create a new S3 bucket or reuse an existing S3 bucket in your chosen AWS region where you want to deploy the Lambda function. This S3 bucket will store the Lambda function ZIP file and packaged CloudFormation template. Note the S3 bucket name.
1. Launch an Amazon Linux 2 x86 EC2 instance in your chosen AWS region, ensuring that you can log into the instance using SSH or Systems Manager Session Manager. Ensure the EC2 Instance Profile for this instance has permissions to upload objects to your S3 bucket, invoke CloudFormation APIs, create IAM Roles, and create Lambda functions.
1. SSH or start a Session Manager session to log into the EC2 instance.
1. Install the development tools group:
```
yum groupinstall development
```
1. Install Python 3.9 by building from the (source)[https://www.python.org/downloads/source/]. See (this post for detailed instructions)[https://computingforgeeks.com/how-to-install-python-on-amazon-linux/].
1. Clone this repository to the EC2 instance:
```
git clone https://github.com/aws-samples/aws-secrets-manager-ssh-key-rotation.git
```
1. Edit the shell script (``deployer.sh``)[deployer.sh] and replace values for these variables to match the S3 bucket you identified above and your chosen AWS region:
```
S3Bucket=BUCKET_NAME
REGION=us-east-1
```
1. Run the shell script to package the Lambda ZIP file, package the CloudFormation SAM template, and deploy the template to your chosen AWS region:
```
sh deployer.sh
```
1. The packaged ZIP file and the packaged CloudFormation template are uploaded to your S3 bucket.
1. Navigate to the CloudFormation console in your chosen AWS region to view the Stack named ``RotateSSH`` and see the resources created, including the rotation Lambda function.
