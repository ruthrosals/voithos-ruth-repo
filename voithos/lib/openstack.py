""" OpenStack lib """
import os

from click import echo

import voithos.lib.aws.s3 as s3
import voithos.lib.aws.ecr as ecr
import voithos.lib.config as config
from voithos.lib.system import shell, error, assert_path_exists, assert_path_does_not_exist
from voithos.lib.docker import volume_opt
from voithos.constants import KOLLA_IMAGE_REPOS
from gnocchiclient.v1 import client as gnocchi
from keystoneauth1 import session
from keystoneauth1.identity import v3


SUPPORTED_IMAGES = [
    "cirros",
    "rhel-6.10",
    "rhel-7.8",
    "rhel-8.2",
    "ubuntu1804",
    "windows10",
    "windows2012",
    "windows2016",
    "windows2019",
    "amphora-train",
    "amphora-wallaby",
]


def kolla_ansible_genpwd(release):
    """ Genereate passwords.yml and print to stdout """
    cwd = os.getcwd()
    path = "/var/repos/kolla-ansible/etc/kolla/passwords.yml"
    cmd = (
        f"docker run --rm "
        f"-v {cwd}:/etc/kolla "
        f"breqwatr/kolla-ansible:{release} "
        f'bash -c "kolla-genpwd --passwords {path} '
        f'&& cp {path} /etc/kolla/passwords.yml"'
    )
    shell(cmd)

def kolla_ansible_merge_passwords(passwords_file, new_release):
    """ Generate passwords file by merging old passwords to
        a newer release password file.
    """
    cwd = os.getcwd()
    new_passwords_path = "/var/repos/kolla-ansible/etc/kolla/passwords.yml"
    old_passwords_path = "/var/repos/kolla-ansible/etc/kolla/old-passwords.yml"
    old_password_vol = volume_opt(passwords_file, f"{old_passwords_path}")
    cmd = (
        f"docker run --rm {old_password_vol} "
        f"-v {cwd}:/etc/kolla "
        f"breqwatr/kolla-ansible:{new_release} "
        f'bash -c "kolla-genpwd --passwords {new_passwords_path} && '
        f'kolla-mergepwd --old {old_passwords_path} --new {new_passwords_path} '
        f'--final /etc/kolla/{new_release}-passwords.yml"'
    )
    shell(cmd)

def kolla_ansible_inventory(release):
    """ Print the inventory template for the given release """
    cwd = os.getcwd()
    assert_path_does_not_exist(cwd+"/inventory")
    inventory_file = "/var/repos/kolla-ansible/ansible/inventory/multinode"
    cmd = (
        f"docker run --rm "
        f"-v {cwd}:/etc/kolla "
        f"breqwatr/kolla-ansible:{release} "
        f"cp {inventory_file} /etc/kolla/inventory"
    )
    shell(cmd)


def kolla_ansible_generate_certificates(release, passwords_path, globals_path):
    """ Genereate certificates directory """
    cwd = os.getcwd()
    globals_vol = volume_opt(globals_path, "/etc/kolla/globals.yml")
    password_vol = volume_opt(passwords_path, "/etc/kolla/passwords.yml")
    certs_vol = f"-v {cwd}/certificates:/etc/kolla/certificates"
    cmd = (
        f"docker run --rm {globals_vol} {password_vol} {certs_vol} "
        f"breqwatr/kolla-ansible:{release} "
        "kolla-ansible certificates"
    )
    shell(cmd)


def kolla_ansible_globals(release):
    """ Genereate certificates directory """
    cwd = os.getcwd()
    assert_path_does_not_exist(cwd+"/globals.yml")
    cmd = (
        f"docker run --rm -v {cwd}:/temp-dir "
        f"breqwatr/kolla-ansible:{release} "
        "cp /var/repos/kolla-ansible/etc/kolla/globals.yml temp-dir/"
    )
    shell(cmd)


def kolla_ansible_get_admin_openrc(release, inventory_path, globals_path, passwords_path):
    """ Save the admin-openrc.sh file to current working directory """
    cwd = os.getcwd()
    inv_vol = volume_opt(inventory_path, "/etc/kolla/inventory")
    globals_vol = volume_opt(globals_path, "/etc/kolla/globals.yml")
    passwords_vol = volume_opt(passwords_path, "/etc/kolla/passwords.yml")
    cwd_vol = f"-v {cwd}:/target "
    cmd = (
        "docker run --rm --network host "
        f"{inv_vol} {globals_vol} {passwords_vol} {cwd_vol} "
        f"breqwatr/kolla-ansible:{release} "
        'bash -c "kolla-ansible post-deploy -i /etc/kolla/inventory && '
        'cp /etc/kolla/admin-openrc.sh /target/"'
    )
    shell(cmd)


def cli_exec(release, openrc_path, command, volume=None, debug=False):
    """ Execute <command> using breqwatr/openstack-client:<release>

        Optionally, mount file(s) into the client with the volume arg
    """
    command = "openstack" if command is None else command
    mount = f"-v {volume} " if volume is not None else " "
    openrc_vol = volume_opt(openrc_path, "/admin-openrc.sh")
    image = f"breqwatr/openstack-client:{release}"
    run = f'bash -c "source /admin-openrc.sh && . /var/repos/env/bin/activate && {command}"'
    cmd = f"docker run -it --rm --network host {openrc_vol} {mount} {image} {run}"
    shell(cmd, print_error=False, print_cmd=debug)


def smoke_test(release, openrc, image_path, **kwargs):
    """ Run the smoke test """
    assert_path_exists(image_path)
    image_vol = volume_opt(image_path, "/image.qcow2")
    openrc_vol = volume_opt(openrc, "/admin-openrc.sh")
    env_var_list = []
    for kwarg in kwargs:
        key = kwarg.upper()
        value = kwargs[kwarg]
        var = f"-e {key}={value}"
        env_var_list.append(var)
    env_vars_str = " ".join(env_var_list)
    run = (
        'bash -c "'
        "source /admin-openrc.sh && "
        ". /var/repos/env/bin/activate && "
        'bash /smoke-test.sh"'
    )
    cmd = (
        "docker run --rm "
        f"{openrc_vol} {image_vol} {env_vars_str} "
        f"breqwatr/openstack-client:{release} {run}"
    )
    shell(cmd)


def kolla_ansible_exec(
    release,
    inventory_path,
    globals_path,
    passwords_path,
    ssh_key_path,
    certificates_dir,
    config_dir,
    command,
    tag=None,
    overrides=None
):
    """ Execute kolla-ansible commands """
    valid_cmds = [
        "deploy",
        "mariadb_recovery",
        "prechecks",
        "post-deploy",
        "pull",
        "reconfigure",
        "upgrade",
        "check",
        "stop",
        "deploy-containers",
        "prune-images",
        "bootstrap-servers",
        "destroy",
        "destroy --yes-i-really-really-mean-it",
        "DEBUG",
    ]
    if command not in valid_cmds:
        error(f'ERROR: Invalid command "{command}" - Valid commands: {valid_cmds}', exit=True)
    config_vol = " "
    if config_dir is not None:
        config_vol = volume_opt(config_dir, "/etc/kolla/config")
    rm_arg = ""
    inv_vol = volume_opt(inventory_path, "/etc/kolla/inventory")
    globals_vol = volume_opt(globals_path, "/etc/kolla/globals.yml")
    passwd_vol = volume_opt(passwords_path, "/etc/kolla/passwords.yml")
    ssh_vol = volume_opt(ssh_key_path, "/root/.ssh/id_rsa")
    cert_vol = volume_opt(certificates_dir, "/etc/kolla/certificates")
    if command == "DEBUG":
        name = f"kolla-ansible-{release}"
        rm_arg = f"-d --name {name}"
        run_cmd = "tail -f /dev/null"
        shell(f"docker rm -f {name} 2>/dev/null || true")
        print(f"Starting persistent container named {name} for debugging")
    else:
        run_cmd = f"kolla-ansible {command} -i /etc/kolla/inventory"
        rm_arg = "--rm"
    tag_opt = "" if tag is None else f"--tag {tag}"
    override_vol_mnt = ""
    if overrides is not None:
        override_vol_mnt = volume_opt(overrides, '/overrides')
        run_cmd = f"bash -c 'cp -r overrides/* / && {run_cmd}'"
    cmd = (
        f"docker run {rm_arg} --network host {override_vol_mnt} "
        "-e PY_COLORS=1 -e ANSIBLE_FORCE_COLOR=1 "
        f"{inv_vol} {globals_vol} {passwd_vol} {ssh_vol} {cert_vol} {config_vol}"
        f"breqwatr/kolla-ansible:{release} {run_cmd} {tag_opt}"
    )
    shell(cmd)


def _sync_image(repo, release, keep, registry, prefered_repo):
    """ Sync a single image to the registry """
    dh_image = f"breqwatr/{repo}:{release}"
    local_image = f"{registry}/{dh_image}"
    if prefered_repo == "ecr":
        ecr.pull(dh_image)
    else:
        shell(f"docker pull {dh_image}")
    shell(f"docker tag {dh_image} {local_image}")
    shell(f"docker push {local_image}")
    if not keep:
        echo(f"Deleting local images {dh_image} and {local_image}")
        shell(f"docker rmi {dh_image}")
        shell(f"docker rmi {local_image}")


def sync_local_registry(release, keep, registry, image=None):
    """ Pull Kolla docker images and push them to local registry """
    prefered_repo = config.get_repo_type()
    if release not in KOLLA_IMAGE_REPOS:
        error(f"ERROR: release {release} is not supported", exit=True)
    total_images = len(KOLLA_IMAGE_REPOS[release])
    index = 1
    if image is not None:
        if image not in KOLLA_IMAGE_REPOS[release]:
            if f"ubuntu-source-{image}" in KOLLA_IMAGE_REPOS[release]:
                image = f"ubuntu-source-{image}"
            else:
                error(f"Invalid repository {image}", exit=True)
        _sync_image(image, release, keep, registry, prefered_repo)
        return
    for repo in KOLLA_IMAGE_REPOS[release]:
        echo(f"Progress: {index}/{total_images} - Image: {repo}")
        _sync_image(repo, release, keep, registry, prefered_repo)
        index += 1


def download_image(image, output_path=None):
    """ Download an OpenStack image from S3. Save to ./ unless output is not None """
    if image not in SUPPORTED_IMAGES:
        raise NotImplementedError(f"Image {image} is not implemented")
    filename = f"{image}.qcow2"
    path = f"./{filename}" if output_path is None else output_path
    bucket = "breqwatr-private-vm-images"
    echo(f"Downloading {path}, please wait. This may take a while...")
    s3.download(path, bucket, filename)


def purge_gnocchi_resources():
    """ Purge all gnocchi resources"""
    gnocchi_client = _get_gnocchiclient()
    all_resources = gnocchi_client.resource.list()
    for resource in all_resources:
        query_str = "id={}".format(resource["id"])
        gnocchi_client.resource.batch_delete(query=query_str)


def _get_gnocchiclient():
    """Return a project scoped gnocchi client"""
    if not all(
        env in os.environ
        for env in (
            "OS_PROJECT_NAME",
            "OS_USER_DOMAIN_NAME",
            "OS_PROJECT_DOMAIN_NAME",
            "OS_AUTH_URL",
            "OS_USERNAME",
            "OS_PASSWORD",
        )
    ):
        error("ERROR: RC file not sourced", exit=True)
    auth = v3.Password(
        auth_url=os.environ["OS_AUTH_URL"],
        username=os.environ["OS_USERNAME"],
        password=os.environ["OS_PASSWORD"],
        project_name=os.environ["OS_PROJECT_NAME"],
        user_domain_name=os.environ["OS_USER_DOMAIN_NAME"],
        project_domain_name=os.environ["OS_PROJECT_DOMAIN_NAME"],
    )
    new_session = session.Session(auth=auth, verify=False)
    gnocchi_client = gnocchi.Client(session=new_session)
    return gnocchi_client
