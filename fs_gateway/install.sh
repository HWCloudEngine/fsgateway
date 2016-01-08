cd "$(dirname $0)"

cp fs-gateway-api fs-gateway-proxy fs-gateway-manage /usr/bin

# create  log directory
mkdir -p /var/log/fusionsphere/component/fs-gateway

# config file
# mkdir /etc/fs-gateway
# cp fs-gateway.conf fs-gateway-paste.ini /etc/fs-gateway

# create fs_gateway database
#su gaussdba -c "cd;/opt/gaussdb/app/bin/gsql -W FusionSphere123  POSTGRES -c 'CREATE DATABASE fs_gateway OWNER openstack;' "

# create fs_gateway db tables
#python ./fs-gateway-manage --config-file=/etc/fs-gateway/fs-gateway.conf db sync

