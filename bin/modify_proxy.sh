#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
dir=${dir}/modify_proxy

rm -rf ${dir}
mkdir -p ${dir}

RUN_SCRIPT=${dir}/modify_proxy_run.sh
LOG=${dir}/modify_proxy_run.log

az_localaz=${1}
az_localdz=${2}
postfix=${3}
proxy_host_id=${4}
proxy=${5}

az_region=${az_localaz}"."${az_localdz}
az_domain=${az_localaz}"."${az_localdz}"."${postfix}

cascading_az=`cps localdomain-get | grep localaz | awk -F "|" '{print $3}' | awk '{gsub(/ /,"")}1'`
cascading_dc=`cps localdomain-get | grep localdc | awk -F "|" '{print $3}' | awk '{gsub(/ /,"")}1'`
cascading_postfix=`cps localdomain-get | grep domainpostfix | awk -F "|" '{print $3}' | awk '{gsub(/ /,"")}1'`

cascading_region=${cascading_az}"."${cascading_dc}
cascading_domain=${cascading_az}"."${cascading_dc}"."${cascading_postfix}

echo "#!/usr/bin/env bash" > ${RUN_SCRIPT}
echo "cps role-host-add --host ${proxy_host_id} dhcp" >> ${RUN_SCRIPT}
echo "cps role-host-add --host ${proxy_host_id} blockstorage-${proxy}" >> ${RUN_SCRIPT}
echo "cps role-host-add --host ${proxy_host_id} compute-${proxy}" >> ${RUN_SCRIPT}
echo "cps role-host-add --host ${proxy_host_id} network-${proxy}" >> ${RUN_SCRIPT}
echo "cps commit" >> ${RUN_SCRIPT}
echo "sleep 10s" >> ${RUN_SCRIPT}

echo "cps template-params-update --parameter host=${az_region} --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter cascaded_glance_url=https://image.${cascading_domain} --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter cascading_nova_url=https://compute.${cascading_domain}:443/v2 --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter cinder_endpoint_template=https://volume.${cascading_domain}:443/v2/%'('project_id')'s --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter neutron_admin_auth_url=https://identity.${cascading_domain}:443/identity/v2.0 --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter keystone_auth_url=https://identity.${cascading_domain}:443/identity/v2.0 --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter os_region_name=${cascading_region} --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter proxy_region_name=${az_region} --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter default_availability_zone=${az_region} --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter default_schedule_zone=${az_region} --service nova nova-${proxy}" >> ${RUN_SCRIPT}

echo "cps template-params-update --parameter cascaded_cinder_url=http://gateway--volume.${az_domain}:8899/v2 --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter cascaded_neutron_url=http://gateway--network.${az_domain}:8899/ --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter cascaded_nova_url=http://gateway--compute.${az_domain}:8899/v2 --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter proxy_region_name=gateway--${az_region} --service nova nova-${proxy}" >> ${RUN_SCRIPT}
echo "cps commit" >> ${RUN_SCRIPT}
echo "sleep 2s" >> ${RUN_SCRIPT}

echo "cps template-params-update --parameter host=${az_region} --service neutron neutron-l2-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter region_name=${az_region} --service neutron neutron-l2-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter neutron_admin_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service neutron neutron-l2-${proxy}" >> ${RUN_SCRIPT}

echo "cps template-params-update --parameter neutron_region_name=gateway--${az_region} --service neutron neutron-l2-${proxy}" >> ${RUN_SCRIPT}
echo "cps commit" >> ${RUN_SCRIPT}
echo "sleep 2s" >> ${RUN_SCRIPT}

echo "cps template-params-update --parameter host=${az_region} --service neutron neutron-l3-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter region_name=${az_region} --service neutron neutron-l3-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter neutron_admin_auth_url=https://identity.${cascading_domain}:443/identity-admin/v2.0 --service neutron neutron-l3-${proxy}" >> ${RUN_SCRIPT}

echo "cps template-params-update --parameter neutron_region_name=gateway--${az_region} --service neutron neutron-l3-${proxy}" >> ${RUN_SCRIPT}
echo "cps commit" >> ${RUN_SCRIPT}
echo "sleep 2s" >> ${RUN_SCRIPT}

echo "cps template-params-update --parameter cascaded_cinder_url=https://volume.${az_domain}:443/v2/%'('project_id')'s --service cinder cinder-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service cinder cinder-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter host=${az_region} --service cinder cinder-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter keystone_auth_url=https://identity.${cascading_domain}:443/identity/v2.0 --service cinder cinder-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter storage_availability_zone=${az_region} --service cinder cinder-${proxy}" >> ${RUN_SCRIPT}

echo "cps template-params-update --parameter cascaded_region_name=gateway--${az_region} --service cinder cinder-${proxy}" >> ${RUN_SCRIPT}
echo "cps commit" >> ${RUN_SCRIPT}
echo "sleep 2s" >> ${RUN_SCRIPT}

echo "cps template-params-update --parameter keystone_auth_url=https://identity.${cascading_domain}:443/identity/v2.0 --service cinder cinder-backup-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter glance_host=https://image.${cascading_domain} --service cinder cinder-backup-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter host=${az_region} --service cinder cinder-backup-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter cascaded_cinder_url=https://volume.${az_domain}:443/v2/%'('project_id')'s --service cinder cinder-backup-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter cascaded_region_name=${az_region} --service cinder cinder-backup-${proxy}" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter storage_availability_zone=${az_region} --service cinder cinder-backup-${proxy}" >> ${RUN_SCRIPT}
echo "cps commit" >> ${RUN_SCRIPT}
echo "sleep 2s" >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${LOG} 2>&1

temp=`cat ${LOG} | grep refused`
if [ -n "${temp}" ]; then
    exit 127
fi
exit 0

