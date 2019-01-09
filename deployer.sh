#!/usr/bin/env bash
S3Bucket=BUCKET_NAME
REGION=us-east-2

FILE="$(uuidgen).yaml"
PREFIX=rotatessh

cd lambda/
pip install -r requirements.txt -t "$PWD" --upgrade
cd ..
aws cloudformation package --region $REGION --template-file secretsmanager_rotate_ssh_keys.template --s3-bucket $S3Bucket --s3-prefix $PREFIX --output-template-file $FILE
aws cloudformation deploy --region $REGION --template-file $FILE --stack-name RotateSSH --capabilities CAPABILITY_NAMED_IAM
