cd "$(dirname $0)"

cp fs-gateway-api fs-gateway-proxy /usr/bin

# create  log directory
mkdir -p /var/log/fusionsphere/component/fs-gateway

# config file
mkdir /etc/fs-gateway
for f in fs-gateway.conf fs-gateway-paste.ini ; do
    cp $f /etc/fs-gateway
done 

# create fs_gateway database
su gaussdba -c "cd;/opt/gaussdb/app/bin/gsql -W FusionSphere123  POSTGRES -c 'CREATE DATABASE fs_gateway OWNER openstack;' "

# create fs_gateway db tables
python ./gw-manage --config-file=/etc/fs-gateway/fs-gateway.conf db sync

