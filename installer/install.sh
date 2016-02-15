#!/usr/bin/env bash
log=$(dirname "$0")/fs_gateway_install.log
dir="$(builtin cd $(dirname '$0')/..; pwd)"
bin_dir=${dir}/bin
etc_dir=${dir}/etc/fs-gateway
fs_gateway_dir=${dir}/fs_gateway
fs_gateway_client_dir=${dir}/fs_gatewayclient

script_install_dir=/home
binary_install_dir=/usr/bin

database_ip="$(awk -F'[:@]' '/^connection/&&$0=$(NF-1)' /etc/nova/nova-api.conf)"

install() {
    echo "install fs_gateway..." 
    ##
    old_dir="$(pwd)"
    
    cd ${fs_gateway_dir} 
    # in case Windows add \r into bash scripts
    dos2unix fs-gateway-api fs-gateway-proxy fs-gateway-manage 

    cp fs-gateway-api fs-gateway-proxy fs-gateway-manage "${binary_install_dir}"

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

    dos2unix fs-gateway.conf fs-gateway-paste.ini
    cp fs-gateway.conf fs-gateway-paste.ini /etc/fs-gateway
    chown -R openstack:openstack /etc/fs-gateway

    cd "$old_dir"
 
    cp -r ${fs_gateway_dir} /usr/lib64/python2.6/site-packages/
    cp -r ${fs_gateway_client_dir} /usr/lib64/python2.6/site-packages/
   
    cp ${fs_gateway_client_dir}/fs-gateway "${binary_install_dir}"/fs-gateway
        
    echo "export FS_GATEWAYCLIENT_BYPASS_URL=http://127.0.0.1:7027/v1.0" >> ~/.bashrc
    
    for binary in fs-gateway-api fs-gateway-proxy fs-gateway-manage fs-gateway ; do 
       chmod +x "${binary_install_dir}"/$binary
    done
  
    echo "start fs_gateway watchdog..." 
    dos2unix ${dir}/bin/fs_gateway_watchdog.sh

    cp ${dir}/bin/fs_gateway_watchdog.sh "${binary_install_dir}"/
    chmod 755 "${binary_install_dir}"/fs_gateway_watchdog.sh

    crontab -l > ${dir}/installer/crontab.bak
    sed -i '/#.*/d' ${dir}/installer/crontab.bak
    echo "* * * * * ${binary_install_dir}/fs_gateway_watchdog.sh >> /var/log/fs_gateway_watchdog.log" >> ${dir}/installer/crontab.bak
    crontab ${dir}/installer/crontab.bak

    
    # create fs_gateway database
    /opt/gaussdb/app/bin/gsql -U openstack -W FusionSphere123  -h "$database_ip" POSTGRES -c 'CREATE DATABASE fs_gateway OWNER openstack;'
    # create fs_gateway db tables
    python "${binary_install_dir}"/fs-gateway-manage --config-file=/etc/fs-gateway/fs-gateway.conf db sync && {
    echo "start fs_gateway api and rest services"
        
        (/usr/bin/python "${binary_install_dir}"/fs-gateway-api --config-file=/etc/fs-gateway/fs-gateway.conf 2>/dev/null &)
        (/usr/bin/python "${binary_install_dir}"/fs-gateway-proxy --config-file=/etc/fs-gateway/fs-gateway.conf 2>/dev/null &)
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
    rm "${binary_install_dir}"/fs_gateway_watchdog.sh

    echo "stop fs_gateway..." 
    pkill -f fs-gateway-proxy
    pkill -f fs-gateway-api

    echo "uninstall fs_gateway..." 
    # drop fs_gateway database
    /opt/gaussdb/app/bin/gsql -U openstack -W FusionSphere123  -h "$database_ip" POSTGRES -c 'drop DATABASE fs_gateway;'
    
    for binary in fs-gateway-api fs-gateway-proxy fs-gateway-manage fs-gateway ; do 
       rm "${binary_install_dir}"/$binary
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
    cp ${dir}/installer/fs_gateway_register.py "${binary_install_dir}"/fs_gateway_register
    chmod +x "${binary_install_dir}"/fs_gateway_register
    local dst_dir="${script_install_dir}/fs_gateway"

    [ "z${dir}" != "z${dst_dir}" ] && {
        mkdir -p ${dst_dir}
        cp -r ${bin_dir} ${dst_dir}
    }
    cp /root/adminrc ${dst_dir}/bin/
    chmod 755 ${dst_dir}/bin/*
    dos2unix ${dst_dir}/bin/*.sh
    chown -R openstack:openstack ${dst_dir}
    echo "install fs_gateway register success." 
}

uninstall_register() {
    
     echo "uninstall fs_gateway register..." 
     rm "${binary_install_dir}"/fs_gateway_register
     rm /usr/lib64/python2.6/site-packages/fs_gateway_register.py
     local dst_dir="${script_install_dir}/fs_gateway"

     [ "z${dir}" != "z${dst_dir}" ] && [ -d "$dst_dir" ] &&  {
         rm -rf ${dst_dir}/bin
         rmdir ${dst_dir}
     }
     echo "uninstall fs_gateway register success." 
    
}
usage() {
    cat <<-EOF
    $0 install|uninstall|install_register|uninstall_register|install_all|uninstall_all
	EOF
    exit 1
}
echo "operate $1, check by $log $(date)"
{
    echo "operate $1 $(date)"
    case "$1" in
    install) 
        uninstall
        install
    ;;
    uninstall) 
        uninstall
    ;;
    install_register)
        uninstall_register
        install_register
    ;;
    uninstall_register)
        uninstall_register
    ;;
    install_all)
        uninstall
        install
        uninstall_register
        install_register
    ;;
    uninstall_all)
        uninstall
        uninstall_register
    ;;
    *) 
        usage
    ;;
    esac
} >>$log 2>&1
