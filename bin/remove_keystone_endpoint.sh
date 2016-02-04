#!/usr/bin/env bash

cd "$(dirname '$0')";

RUN_LOG=remove_keystone_endpoint.log

[ $# -lt 3 ] && { echo "$0 az01 shenzhen--fusionsphere huawei.com" ; exit 1; }

az_localaz=${1}
az_localdz=${2}
postfix=${3}
az_region=${az_localaz}"."${az_localdz}

. /root/adminrc

try_times=10
echo "delete endpoint-list $(date)" >> ${RUN_LOG}
for id in $(keystone endpoint-list | awk  '/'"$az_region"'/&&$0=$2') ; do
	for((i=0;i<$try_times;i++)) ; do 
     echo "delete keystone endpoint $id ${i}th time"
     keystone endpoint-delete $id | grep deleted && break
     sleep 1
  done
done > ${RUN_LOG} 2>&1

