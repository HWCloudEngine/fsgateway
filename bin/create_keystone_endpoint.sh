#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
cd "${dir}"
dir=${dir}/create_keystone_endpoint

rm -rf ${dir}
mkdir -p ${dir}

#RUN_SCRIPT=${dir}/create_keystone_endpoint_run.sh
#RUN_LOG=${dir}/create_keystone_endpoint_run.log
RUN_LOG=create_keystone_endpoint.log

cloud_az=${1}
cloud_dc=${2}
postfix=${3}

cloud_region=${cloud_az}"."${cloud_dc}
cloud_domain=${cloud_az}"."${cloud_dc}"."${postfix}

v2v_gw_ip=${4}

. adminrc
keystone service-list > ${dir}/keystone_service_list.temp
temp=`cat ${dir}/keystone_service_list.temp`
for i in {1..10}
do
    if [ -n "${temp}" ]; then
        break
    else
        . adminrc
        keystone service-list > ${dir}/keystone_service_list.temp
        temp=`cat ${dir}/keystone_service_list.temp`
    fi
done

if [ -z "${temp}" ]; then
    exit 127
fi

cps_id=`awk -F "|" '{if($4~/ cps /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${cps_id}" ]; then
    sleep 0.5s
    cps_id=`keystone service-list | awk -F "|" '{if($4~/ cps /) print $2}'`
fi


log_id=`awk -F "|" '{if($4~/ log /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${log_id}" ]; then
    sleep 0.5s
    log_id=`keystone service-list | awk -F "|" '{if($4~/ log /) print $2}'`
fi

oam_id=`awk -F "|" '{if($4~/ oam /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${oam_id}" ]; then
    sleep 0.5s
    oam_id=`keystone service-list | awk -F "|" '{if($4~/ oam /) print $2}'`
fi

volume_v2_id=`awk -F "|" '{if($4~/ volumev2 /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${volume_v2_id}" ]; then
    sleep 0.5s
    volume_v2_id=`keystone service-list | awk -F "|" '{if($4~/ volumev2 /) print $2}'`
fi

upgrade_id=`awk -F "|" '{if($4~/ upgrade /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${upgrade_id}" ]; then
    sleep 0.5s
    upgrade_id=`keystone service-list | awk -F "|" '{if($4~/ upgrade /) print $2}'`
fi

compute_id=`awk -F "|" '{if($4~/ compute /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${compute_id}" ]; then
    sleep 0.5s
    compute_id=`keystone service-list | awk -F "|" '{if($4~/ compute /) print $2}'`
fi

backup_id=`awk -F "|" '{if($4~/ backup /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${backup_id}" ]; then
    sleep 0.5s
    backup_id=`keystone service-list | awk -F "|" '{if($4~/ backup /) print $2}'`
fi

orchestration_id=`awk -F "|" '{if($4~/ orchestration /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${orchestration_id}" ]; then
    sleep 0.5s
    orchestration_id=`keystone service-list | awk -F "|" '{if($4~/ orchestration /) print $2}'`
fi

info_collect_id=`awk -F "|" '{if($4~/ collect /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${info_collect_id}" ]; then
    sleep 0.5s
    info_collect_id=`keystone service-list | awk -F "|" '{if($4~/ collect /) print $2}'`
fi

object_store_id=`awk -F "|" '{if($4~/ object-store /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${object_store_id}" ]; then
    sleep 0.5s
    object_store_id=`keystone service-list | awk -F "|" '{if($4~/ object-store /) print $2}'`
fi

volume_id=`awk -F "|" '{if($4~/ volume /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${volume_id}" ]; then
    sleep 0.5s
    volume_id=`keystone service-list | awk -F "|" '{if($4~/ volume /) print $2}'`
fi

network_id=`awk -F "|" '{if($4~/ network /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${network_id}" ]; then
    sleep 0.5s
    network_id=`keystone service-list | awk -F "|" '{if($4~/ network /) print $2}'`
fi

metering_id=`awk -F "|" '{if($4~/ metering /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${metering_id}" ]; then
    sleep 0.5s
    metering_id=`keystone service-list | awk -F "|" '{if($4~/ metering /) print $2}'`
fi

v2v_id=`awk -F "|" '{if($4~/ v2v /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${metering_id}" ]; then
    sleep 0.5s
    v2v_id=`keystone service-list | awk -F "|" '{if($4~/ v2v /) print $2}'`
fi

glance_id=`awk -F "|" '{if($4~/ image /) print $2}' ${dir}/keystone_service_list.temp`
if [ -z "${glance_id}" ]; then
    sleep 0.5s
    glance_id=`keystone service-list | awk -F "|" '{if($4~/ image /) print $2}'`
fi

try_times=10

keystone_create() {
		extra_params="--service $1 --publicurl $2"
		[ e$3 != e ] && extra_params="$extra_params --internalurl $3"
		[ e$4 != e ] && extra_params="$extra_params --adminurl $4"
		 for((i=0;i<$try_times;i++)) ; do  
				echo -n "try create endpoint ${i}th "
				keystone endpoint-create --region ${cloud_region} $extra_params | awk '$2=="id"&&$0=$4' && break
				sleep 1;
		done
		[ z"$i" = z"$try_times" ] && { echo "create keystone endpoint id $2 total failed" ; exit 127; }
		[ "a$5" = agw ] && {
			   gw_public="$(echo $2 | sed 's@https://@http://gateway--@;s@443@8899@')"
				 for((i=0;i<$try_times;i++)) ; do 
						echo -n "try create gateway ${i}th "
						keystone endpoint-create --region gateway--${cloud_region} --service $1 --publicurl $gw_public | awk '$2=="id"&&$0=$4' && break
						sleep 1;
				done
				[ z"$i" = z"$try_times" ] && { echo "create keystone endpoint id $2 total failed" ; exit 127; }
		}

}

{
		keystone_create ${cps_id} "https://cps.${cloud_domain}:443" https://cps.localdomain.com:8008 "https://cps.${cloud_domain}:443"  

		keystone_create ${log_id} "https://log.${cloud_domain}:443"  "https://log.localdomain.com:8232" "https://log.${cloud_domain}:443" 

		keystone_create ${oam_id}  "https://oam.${cloud_domain}:443"   "https://oam.localdomain.com:8200"  "https://oam.${cloud_domain}:443" 

		keystone_create ${volume_v2_id}  "https://volume.${cloud_domain}:443/v2/"'$(tenant_id)s'   'https://volume.localdomain.com:8776/v2/$(tenant_id)s'  "https://volume.${cloud_domain}:443/v2/"'$(tenant_id)s' gw

		keystone_create ${upgrade_id}  "https://upgrade.${cloud_domain}:443"   "https://upgrade.localdomain.com:8100"  "https://upgrade.${cloud_domain}:443" 

		keystone_create ${compute_id}  "https://compute.${cloud_domain}:443/v2/"'$(tenant_id)s'   'https://compute.localdomain.com:8001/v2/$(tenant_id)s'  "https://compute.${cloud_domain}:443/v2/"'$(tenant_id)s' gw

		keystone_create ${backup_id}  "https://backup.${cloud_domain}:443"   "https://backup.localdomain.com:8888"  "https://backup.${cloud_domain}:443" 

		keystone_create ${orchestration_id}  "https://orchestration.${cloud_domain}:443/v1/"'$(tenant_id)s'   'https://orchestration.localdomain.com:8700/v1/$(tenant_id)s'  "https://orchestration.${cloud_domain}:443/v1/"'$(tenant_id)s' 

		keystone_create ${info_collect_id}  "https://info-collect.${cloud_domain}:443"   "https://info-collect.localdomain.com:8235"  "https://info-collect.${cloud_domain}:443" 

		keystone_create ${object_store_id}  "https://object-store.${cloud_domain}:443/v1/AUTH_"'$(tenant_id)s'   'http://object-store.localdomain.com:8006/v1/AUTH_$(tenant_id)s'  "http://object-store.${cloud_domain}:443/v1/AUTH_"'$(tenant_id)s' 

		keystone_create ${volume_id}  "https://volume.${cloud_domain}:443/v2/"'$(tenant_id)s'   'https://volume.localdomain.com:8776/v2/$(tenant_id)s'  "https://volume.${cloud_domain}:443/v2/"'$(tenant_id)s' gw

		keystone_create ${network_id}  "https://network.${cloud_domain}:443"   "https://network.localdomain.com:8020"  "https://network.${cloud_domain}:443" gw

		keystone_create ${metering_id}  "https://metering.${cloud_domain}:443"   "https://metering.localdomain.com:8777"  "https://metering.${cloud_domain}:443" 

		keystone_create ${v2v_id}  "http://${v2v_gw_ip}:8090/"   "http://${v2v_gw_ip}:8090/"  "http://${v2v_gw_ip}:8090/" 

		keystone_create ${glance_id}  "https://image.${cloud_domain}:443"
} > ${RUN_LOG} 2>&1

true
