#!/usr/bin/env bash

for ((i=0;i<=59;i++));
do
    for bin in proxy api ; do 
        if  ! pgrep -f fs-gateway-$bin >/dev/null ;
        then
            (/usr/bin/python /usr/bin/fs-gateway-$bin --config-file=/etc/fs-gateway/fs-gateway.conf > /dev/null 2>&1 &)
            echo "restart fs_gateway-$bin...  $(date)"
        fi
    done
    sleep 1s
done
