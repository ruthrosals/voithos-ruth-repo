# Kolla-Ansible Globals.yml

Writing the `globals.yml` file is the most complicated step when deploying OpenStack. This page
covers the options Breqwatr generally chooses. Combine everything that would apply to your
deployment into one `globals.yml` file.

This information is accurate for the Train release of OpenStack.
When in doubt, check the [official globals.yml template on GitHub](https://github.com/openstack/kolla-ansible/blob/stable/train/etc/kolla/globals.yml)
for your release.

## Docker & Image config

```yaml
# prefix for image names (breqwatr/<image>)
docker_namespace: breqwatr

# Offline install settings.
# Keep docker_apt_key_id empty
docker_apt_key_id:
docker_apt_url:  "http://<apt url with port>"
docker_apt_repo: "deb [trusted=yes arch=amd64] <docker_apt_url> <ubuntu-release> stable"
docker_apt_package: "docker-ce=5:19.03.12~3-0~ubuntu-bionic"

# openstack release
openstack_release: train

# These are always going to be the same - we build all images as ubuntu-source
kolla_base_distro: ubuntu
kolla_install_type: source

# Optionally, define a local registry
#docker_registry:
#docker_registry_insecure: "{{ 'yes' if docker_registry else 'no' }}"
#docker_registry_username:
#docker_registry_password: <set in the passwords.yml file>
```

## Interface Config

*Reminder*: Neutron needs a dedicated interface. If you give that interface VLAN sub-interfaces,
they’ll work but Neutron won’t be able to use those VLANs. Neutron won’t error out when you try
, they just won’t work.

```yaml
neutron_external_interface: eno2
```

You’ll usually just configure one interface (a bond) for everything “undercloud” as follows:

```yaml
network_interface: eno1
```

For more fine-grained control, look into these  options. They’re explained well
[here](https://github.com/openstack/kolla-ansible/blob/cd3c51197e04d9df5077dcb92e8521efca5e5075/doc/source/admin/production-architecture-guide.rst).

```yaml
#kolla_external_vip_interface: "{{ network_interface }}"
#api_interface: "{{ network_interface }}"
#storage_interface: "{{ network_interface }}"
#cluster_interface: "{{ network_interface }}"
#swift_storage_interface: "{{ storage_interface }}"
#swift_replication_interface: "{{ swift_storage_interface }}"
#tunnel_interface: "{{ network_interface }}"
#dns_interface: "{{ network_interface }}"
#octavia_network_interface: "{{ api_interface }}"
```

## HAProxy

```yaml
enable_haproxy: yes

# Matching internal VIP and external VIP don't work correctly with HTTPS enabled
kolla_same_external_internal_vip: no
kolla_internal_vip_address: <internal vip>
kolla_external_vip_address: <external vip>

kolla_external_fqdn: < external VIP or fqdn>

kolla_enable_tls_internal: no
kolla_enable_tls_external: yes
```

## KeepAlived

It's important to choose a unique VRID on your subnet.

```yaml
enable_keepalived: yes
keepalived_virtual_router_id: <1 to 255>
```

## MariaDB


```yaml
enable_mariadb: yes

```


## Memcached

```yaml
enable_memcached: yes
```


## RabbitMQ

```yaml
enable_rabbitmq: yes
```

## Chrony

```yaml
enable_chrony: yes
```

## Fluentd

```yaml
enable_fluentd: yes
```

## Ceph

While possible, we never use Kolla-Ansible to install Ceph. Instead we prefer Ceph-Ansible.
Set external_ceph_cephx_enabled to "yes" if ceph is deployed separately.

```yaml
enable_ceph: no
external_ceph_cephx_enabled:

# Update the pool names below if pools are created with some other names.
# ceph_nova_user feild required after Victoria release
ceph_nova_user: "nova"
ceph_nova_pool_name: "volumes"
ceph_nova_keyring: "ceph.client.nova.keyring"
ceph_cinder_user: "cinder"
ceph_cinder_pool_name: "volumes"
ceph_cinder_keyring: "ceph.client.cinder.keyring"
ceph_nova_user: "glance"
ceph_nova_pool_name: "images"
ceph_nova_keyring: "ceph.client.glance.keyring"
# If gnocchi is enabled
ceph_gnocchi_user: "gnocchi"
ceph_gnocchi_pool_name: "gnocchi"
ceph_gnocchi_keyring: "ceph.client.gnocchi.keyring"
```



## Keystone

```yaml
enable_keystone: yes

keystone_admin_user: admin
keystone_admin_project: admin
```

## Nova

```yaml
enable_nova: yes
enable_nova_ssh: yes

# Compute type is "kvm" for metal, "qemu" when running OpenStack in a VM
nova_compute_virt_type: kvm

#nova_backend_ceph: no
```

## Placement

```yaml
enable_placement: yes
```

## Neutron

```yaml
enable_neutron: yes
enable_neutron_provider_networks: yes

# enable_neutron_agent_ha enables ha for dhcp and l3 agent
enable_neutron_agent_ha: yes
neutron_extension_drivers:
  - name: port_security
    enabled: true
  - name: dns
    enabled: true
```

## Glance

```yaml
enable_glance: yes

#glance_backend_ceph: no
#glance_backend_file: yes

# This isn't useful with Ceph but can be useful for iscsi storage appliances
# We haven't tested it, don't use it in production yet
#enable_glance_image_cache: no
```

## Cinder

Don’t use both Ceph and LVM backends at the same time.


```yaml
enable_cinder: yes
enable_cinder_backup: no

#cinder_backend_ceph: no

#enable_cinder_backend_lvm: no
#cinder_volume_group: cinder-volumes

# For Pure Storage/EMC and LVM, enable backend_iscsi
#enable_cinder_backend_iscsi: <yes or no>
```

## iscsid

```yaml
# set enable_iscsid to yes when enable_cider and enable_cinder_backend_iscsi equal yes
enable_iscsid: no
```

## Prometheus

```yaml
enable_prometheus: yes
# Prometheus cli flags
prometheus_cmdline_extras: "-storage.local.retention 360h -storage.local.target-heap-size 2147483648"
```
Values assigned to flags above are default values. Retention time can be changed
according to requirement. Default value of heap size is fine for 4 or 5 nodes cloud.
Increase it according to number of nodes sending data to prometheus-server. It's just an estimate.
In order to calculate it precisely, we need to know total number of timeseries.
For more information check https://prometheus.io/docs/prometheus/1.8/storage/#settings-for-high-numbers-of-time-series

For supported flags in prometheus v1.8, check [**this**](/prometheus-flags.html)

## Grafana

```yaml
enable_grafana: yes
```

## Horizon

Only enable Horizon if you won't be putting Arcus on ports 80 and 443 of the control nodes.

```yaml
enable_horizon: yes
```

## Gnocchi
Gnocchi depends on ceilometer for polling metrics. Enable both gnocchi and ceilometer.

```yaml
enable_ceilometer: yes
enable_gnocchi: yes
gnocchi_backend_storage: "ceph" or "file"
```

## Central Logging

Central logging deploys elasticsearch and kibana. If enabling elasticsearch_curator, you can also
set soft and hard retention time. Indices are closed after soft retention period and deleted after
hard retention period.
```yaml
enable_central_logging: "yes"
enable_elasticsearch_curator: "yes"
elasticsearch_curator_soft_retention_period_days: 15
elasticsearch_curator_hard_retention_period_days: 15
```
Older checkouts of kolla-ansible stable/train weren't supporting elasticsearch curator.
If you are installing elasticsearch curator on an existing cloud, please ensure that
elasticsearch curator hosts are defined in inventory in next step.

## Octavia
Octavia service allows openstack to deploy load balancers.
```yaml
# "enable_neutron_provider_networks" should be yes if enabling octavia. In neutron configs
# section of globals file, check if it's enabled or not.
enable_octavia: "yes"
# octavia_network_interface is the control node interface on which an ip address is configured
# which either belongs to or accessible from loadbalancer management network.
octavia_network_interface: "<network_interface>"
# By default it picks admin for train or earlier release. Newer releases use service project.
# Upgrade may fail because of that. So, it's better to configure "service" as octavia auth project.
octavia_service_auth_project: "service"
```
### Octavia Certificates
Octavia deployment requires amphora certificates. Follow these steps to generate those certs.
- [**Octavia Certificates**](/openstack-octavia-certs.html)

In releases earlier than wallaby, there are some steps that need to be performed after cloud deployment.
These steps include creation of workloads that are required by octavia to create loadbalancers.


- [**Octavia Post-deployment Steps (Optional)**](/openstack-octavia-post-deployment.html)
  **Note**: Steps mentioned in this link will be performed after deployment.
  This link can be seen after the kolla-ansible deployment steps.

Above mentioned procedure for manually creating workloads works for openstack wallaby as well,
but it requires this configuration in globals file
```yaml
octavia_auto_configure: no
```
It can also be automated in wallaby by putting these configs in globals file. This way,
reconfiguration isn't required after deployment.
```yaml
octavia_amp_flavor:
  name: "amphora"
  is_public: no
  vcpus: 1
  ram: 1024
  disk: 0
octavia_amp_network:
  name: ext-net
  provider_network_type: vlan
  provider_segmentation_id: 106
  provider_physical_network: physnet1
  external: yes
  shared: yes
  subnet:
    name: ext-subnet
    cidr: "10.106.0.0/16"
    allocation_pool_start: "10.106.249.1"
    allocation_pool_end: "10.106.249.254"
    gateway_ip: "10.106.0.1"
    enable_dhcp: yes
# Change the subnet info according to your own subnet.
# octavia_network_interface's ip address should either belongs to octavia_amp_network's subnet or
#  accessible from octavia_amp_network's subnet.
```
