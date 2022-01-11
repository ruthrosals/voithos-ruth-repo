""" lib for arcus services """

from voithos.lib.docker import env_string, volume_opt
from voithos.lib.system import shell
from voithos.constants import DEV_MODE


def start(
    release,
    openstack_vip,
    sql_pass,
    sql_ip,
    rabbit_ips_list,
    rabbit_pass,
    enable_ceph,
    kolla_ansible_dir,
    cloud_name,
    idrac_config=None
):
    """ Start the arcus api """
    rabbit_ips_csv = ",".join(rabbit_ips_list)
    image = f"breqwatr/arcus-mgr:{release}"
    env_vars = {
        "OPENSTACK_VIP": openstack_vip,
        "SQL_USERNAME": "arcus",
        "SQL_PASSWORD": sql_pass,
        "SQL_IP": sql_ip,
        "DR_SQL_USERNAME": "arcus",
        "DR_SQL_PASSWORD": sql_pass,
        "DR_SQL_IP": sql_ip,
        "RABBIT_NODES_CSV": rabbit_ips_csv,
        "RABBIT_USERNAME": "openstack",
        "RABBIT_PASSWORD": rabbit_pass,
        "ENABLE_CEPH": str(enable_ceph).lower(),
        "CLOUD_NAME": cloud_name
    }
    network = "--network=host"
    if DEV_MODE:
        network = ""
    env_str = env_string(env_vars)
    name = "arcus_mgr"
    shell(f"docker rm -f {name} 2>/dev/null || true")
    idrac_vol = volume_opt(idrac_config, "etc/arcusmgr/idrac/hosts_cfg.json") if idrac_config else ""
    ka_vol = volume_opt(kolla_ansible_dir, "/etc/kolla")
    cmd = f"docker run -d --restart=always --name {name} {network} {env_str} {ka_vol} {idrac_vol} {image}"
    shell(cmd)
