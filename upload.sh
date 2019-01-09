#!/usr/bin/env bash
S3BUCKET=BUCKET_NAME
REGION=us-east-2
PREFIX=rotatessh

aws s3 cp master_workers.yaml s3://$S3BUCKET/$PREFIX/cfn/ --acl public-read

aws s3 cp --recursive scripts/ s3://$S3BUCKET/$PREFIX/scripts/ --acl public-read
