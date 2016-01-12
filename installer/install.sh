#!/usr/bin/env bash
dir=`cd "$(dirname '$0')"/..; pwd`
bin_dir=${dir}/bin
etc_dir=${dir}/etc/fs-gateway
fs_gateway_dir=${dir}/fs_gateway
fs_gateway_client_dir=${dir}/fs_gatewayclient
log=${dir}/installer/fs_gateway_install.log

dst_dir=/home/fs_gateway
install_dir=/usr/bin

database_ip="$(awk -F'[:@]' '/^connection/&&$0=$(NF-1)' /etc/nova/nova-api.conf)"

install() {
    echo "install fs_gateway..." 
    ##
    old_dir="$(pwd)"
    
    cd ${fs_gateway_dir} 

    cp fs-gateway-api fs-gateway-proxy fs-gateway-manage "${install_dir}"

    # create log directory
    mkdir -p /var/log/fusionsphere/component/fs-gateway

    cd ${etc_dir}
    # config file
    ## correct database address
    database="$(awk '/^connection *=/&&sub("nova$","fs_gateway"){print;exit}' /etc/nova/nova-api.conf)"
    sed -i '/^ *connection *=.*$/c'"$database" fs-gateway.conf
    
    ##    
    cascading_keystone_url=$(cps localdomain-get | awk '{A[$2]=$4}END{print "https://identity."A["localaz"]"."A["localdc"]"."A["domainpostfix"]":443/identity-admin/v2.0"}')
    sed -i '/^ *cascading_keystone_url/s^=.*^'"= $cascading_keystone_url^" fs-gateway.conf
    
    ## mk etc file
    mkdir /etc/fs-gateway

    cp fs-gateway.conf fs-gateway-paste.ini /etc/fs-gateway
    chown -R fsp:fsp /etc/fs-gateway

    cd "$old_dir"
 
    cp -r ${fs_gateway_dir} /usr/lib64/python2.6/site-packages/
    cp -r ${fs_gateway_client_dir} /usr/lib64/python2.6/site-packages/
   
    cp ${fs_gateway_client_dir}/fs-gateway "${install_dir}"/fs-gateway
        
    echo "export FS_GATEWAYCLIENT_BYPASS_URL=http://127.0.0.1:7027/v1.0" >> ~/.bashrc
    
    for binary in fs-gateway-api fs-gateway-proxy fs-gateway-manage fs-gateway ; do 
       chmod +x "${install_dir}"/$binary
    done
  
    echo "start fs_gateway watchdog..." 
    cp ${dir}/bin/fs_gateway_watchdog.sh "${install_dir}"/
    chmod 755 "${install_dir}"/fs_gateway_watchdog.sh

    crontab -l > ${dir}/installer/crontab.bak
    sed -i '/#.*/d' ${dir}/installer/crontab.bak
    echo "* * * * * ${install_dir}/fs_gateway_watchdog.sh >> /var/log/fs_gateway_watchdog.log" >> ${dir}/installer/crontab.bak
    crontab ${dir}/installer/crontab.bak

    
    # create fs_gateway database
    /opt/gaussdb/app/bin/gsql -U openstack -W FusionSphere123  -h "$database_ip" POSTGRES -c 'CREATE DATABASE fs_gateway OWNER openstack;'
    # create fs_gateway db tables
    python "${install_dir}"/fs-gateway-manage --config-file=/etc/fs-gateway/fs-gateway.conf db sync && {
    echo "start fs_gateway api and rest services"
        
        (/usr/bin/python "${install_dir}"/fs-gateway-api --config-file=/etc/fs-gateway/fs-gateway.conf 2>/dev/null &)
        (/usr/bin/python "${install_dir}"/fs-gateway-proxy --config-file=/etc/fs-gateway/fs-gateway.conf 2>/dev/null &)
        true
    } || {
         echo -e "fs gateway database table create failed\nCheck database config in /etc/fs-gateway/fs-gateway.conf"; exit 1
    }
    
    echo "install fs_gateway success."
}

uninstall() {
    echo "stop fs_gateway watchdog..." 
    crontab -l > crontab.bak
    sed -i '/#.*/d' crontab.bak
    sed -i '/.*fs_gateway_watchdog.*/d' crontab.bak
    crontab crontab.bak
    rm "${install_dir}"/fs_gateway_watchdog.sh

    echo "stop fs_gateway..." 
    pkill -f fs-gateway-proxy
    pkill -f fs-gateway-api

    echo "uninstall fs_gateway..." 
    # drop fs_gateway database
    /opt/gaussdb/app/bin/gsql -U openstack -W FusionSphere123  -h "$database_ip" POSTGRES -c 'drop DATABASE fs_gateway;'
    
    for binary in fs-gateway-api fs-gateway-proxy fs-gateway-manage fs-gateway ; do 
       rm "${install_dir}"/$binary
    done

    rm -rf /usr/lib64/python2.6/site-packages/fs_gateway
    rm -rf /usr/lib64/python2.6/site-packages/fs_gatewayclient
    
    rm -rf /etc/fs-gateway/
    rm -rf /var/log/fusionsphere/component/fs-gateway/

    echo "uninstall fs_gateway success."
}

install_register() {
    echo "install fs_gateway register..." 
    chmod +x ${dir}/installer/fs_gateway_register.py
    cp ${dir}/installer/fs_gateway_register.py /usr/lib64/python2.6/site-packages/
    cp ${dir}/installer/fs_gateway_register.py "${install_dir}"/fs_gateway_register
    [ "z${dir}" != "z${dst_dir}" ] && {
        mkdir -p ${dst_dir}
        cp -r ${bin_dir} ${dst_dir}
        chown -R fsp:fsp ${dst_dir}
        chmod 755 ${dst_dir}/bin/*
    }
    echo "install fs_gateway register success." 
}

uninstall_register() {
    
     echo "uninstall fs_gateway register..." 
     rm "${install_dir}"/fs_gateway_register
     rm /usr/lib64/python2.6/site-packages/fs_gateway_register.py

     [ "z${dir}" != "z${dst_dir}" ] &&  rm -f ${dst_dir}/bin/* && rmdir -p ${dst_dir}
     echo "uninstall fs_gateway register success." 
    
}
usage() {
cat <<EOF
   $0 install|uninstall|install_register|uninstall_register|install_all|uninstall_all
EOF
exit 1
}
{
    echo "operate $1 $(date)"
    if [ "z$1" == "zinstall" ]; then
        uninstall
        install
    elif [ "z$1" == "zuninstall" ]; then
        uninstall
    elif [ "z$1" == "zinstall_register" ]; then
        uninstall_register
        install_register
    elif [ "z$1" == "zuninstall_register" ]; then
        uninstall_register
    elif [ "z$1" == "zinstall_all" ]; then
        uninstall
        install
        uninstall_register
        install_register
    elif [ "z$1" == "zuninstall_all" ]; then
        uninstall
        uninstall_register
    else usage;
    fi
} 2>&1 | tee -a $log
