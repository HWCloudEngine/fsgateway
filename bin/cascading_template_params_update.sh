#!/usr/bin/env bash

dir=`cd "$(dirname "$0")"; pwd`
dir=${dir}/cascading_template_params_update

rm -rf ${dir}
mkdir -p ${dir}

RUN_SCRIPT=${dir}/cascading_template_params_update_run.sh
LOG=${dir}/cascading_template_params_update_run.log

. /root/adminrc

echo "#!/usr/bin/env bash" > ${RUN_SCRIPT}
echo "cps template-params-update --parameter scheduler_default_filters=AvailabilityZoneFilter --service nova nova-scheduler" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter lbaas_vip_create_port=True --service neutron neutron-server" >> ${RUN_SCRIPT}
echo "cps template-params-update --parameter mechanism_drivers=openvswitch,l2populationcascading,basecascading,evs,sriovnicswitch,netmapnicswitch --service neutron neutron-server" >> ${RUN_SCRIPT}
echo "cps commit" >> ${RUN_SCRIPT}
keystone service-list | grep v2v || echo ". /root/adminrc; keystone service-create --name v2v --type v2v" >> ${RUN_SCRIPT}

sh ${RUN_SCRIPT} > ${LOG} 2>&1

temp=`cat ${LOG} | grep refused`
if [ -n "${temp}" ]; then
    exit 127
fi
exit 0