from multiprocessing.dummy import Pool

from libcloud.compute.drivers.openstack import OpenStackNodeDriver
from libcloud.container.drivers.docker import DockerContainerDriver

from log import traced, ignored


##############################################################
# Wrapping libcloud in a pythonic, really cloud-agnostic way #
##############################################################

class Cloud:
    @traced('text')
    def __init__(self, cfg):
        """Initialize Cloud"""
        self._cfg = cfg
        self._conn = DockerContainerDriver(key="",
                                           secret="",
                                           host=cfg['auth']['host'],
                                           port=cfg['auth']['port'])
        self._next_free_port = 5099
        self.id = self._cfg['id']
        self.availability = self._cfg['availability']
        self.cost = self._cfg['cost']
        self.location = self._cfg['location']['country']

    def clean_test_setup(self):
        """Remove all deployed Containers"""
        self._destroy_all_containers()

    def request_ip(self):
        """Get the Next Free IP.
           In Docker this is always the same as Host IP."""
        return self._cfg['auth']['host']

    def request_port(self):
        """Get the Next Free Port"""
        # TODO Get dynamically from Driver
        reserved_port = self._next_free_port
        self._next_free_port = reserved_port + 1
        return reserved_port

    @property
    def provider(self):
        """Get Cloud Provider ID"""
        return self._conn.type

    @property
    def images(self):
        """List Images"""
        return self._conn.list_images()

    @property
    def containers(self):
        """List Containers"""
        return self._conn.list_containers(all=True)

    def deploy_template(self, name, template):
        """Deploy Service Instance from Template"""
        return self.deploy(
            name,
            image=template['provider']['docker']['image'],
            command=' '.join(template['provider']['docker']['command']))

    def deploy(self, name, image, command=None, labels=None, remove_existing=True):
        """Deploy Service Instance"""
        existing_container = self._get_container(name)
        if remove_existing and existing_container:
            existing_container.destroy()
        return self._deploy_container(name, image, command, labels)

    @traced()
    def _deploy_container(self, name, image, command=None, labels=None):
        """Deploy Container"""
        return self._conn.deploy_container(name,
                                           image=self._get_image(image),
                                           command=command,
                                           network_mode='host')

    def _get_image(self, path):
        """Get Image by Path"""
        existing_image = next((i for i in self.images if i.path == path), None)
        return existing_image or self._install_image(path)

    @traced()
    def _install_image(self, path):
        """Install Image"""
        return self._conn.install_image(path)

    def _get_container(self, name):
        """Get Container by Name"""
        return next((c for c in self.containers if c.name == name), None)

    @traced('name')
    def _container_log(self, container):
        """Get Docker Container Logs"""
        return self._conn.ex_get_logs(container)

    @traced()
    def _destroy_all_containers(self, stopped=True):
        """Stop and Remove all Containers"""
        # We use dummy.Pool for a simpler threading interface,
        # as we wait for net i/o instead of a calculation,
        # which would actually need multiprocessing.
        with Pool(8) as pool:
            with ignored(Exception):
                pool.map(lambda c: c.stop(), self.containers)
            with ignored(Exception):
                pool.map(lambda c: c.destroy(), self.containers)

    def __repr__(self):
        return "<{name}: id={id}>".format(name=__name__, id=self.id)


class AmazonCloud:
    """This currently fails because of a libcloud error:
    requests.exceptions.ConnectionError: HTTPSConnectionPool(host='ecs.%s.amazonaws.com', port=443): Max retries exceeded with url: / (Caused by NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x7f40f7135668>: Failed to establish a new connection: [Errno -2] Name or service not known',))
    """

    @traced('text')
    def __init__(self, cfg):
        # from libcloud.container.types import Provider
        # from libcloud.container.providers import get_driver
        #
        # from libcloud.container.utils.docker import HubClient
        #
        # """Initialize Cloud"""
        # self._cfg = cfg
        # cls = get_driver(Provider.ECS)
        # hub = HubClient()
        #
        # image = hub.get_image('ubuntu', 'latest')
        # print(image)
        # conn = cls(access_id=cfg['auth']['access_id'],
        #            secret=cfg['auth']['password'],
        #            region=cfg['auth']['region'])
        # self.id = self._cfg['id']
        #
        # for cluster in conn.list_clusters():
        #     print(cluster.name)
        pass

    @property
    def provider(self):
        """Get Cloud Provider ID"""
        return 'ec2'


class DockerCloud:
    pass
    """
    # Docker
    #
    # How-to setup Docker API access on host
    # https://stackoverflow.com/documentation/docker/3935/docker-engine-api#t=201707221117108881869
    #
    # Instead of None, we need to pass empty strings for key and secret, apache/libcloud/pull/1067
    """


class OpenStackCloud:
    @traced('text')
    def __init__(self, cfg):
        """Initialize Cloud"""
        self._cfg = cfg
        self._conn = OpenStackNodeDriver(cfg['auth']['username'],
                                         cfg['auth']['password'],
                                         ex_tenant_name=cfg['auth']['tenant_name'],
                                         ex_force_auth_url=cfg['auth']['url'],
                                         ex_force_auth_version=cfg['auth']['version'],
                                         ex_force_service_region=cfg['auth']['region_name'])

        self.id = self._cfg['id']
        self.availability = self._cfg['availability']
        self.cost = self._cfg['cost']
        self.location = self._cfg['location']['country']

        # DevStack: DO NOT create Volume when deploying
        print(self._conn.list_images())


# TODO: Rename to OpenStack
#
class PowerVcCloud:
    @traced('text')
    def __init__(self, cfg):
        """Initialize Cloud"""

        import libcloud.security

        # The PowerVC certificate is self-signed
        libcloud.security.VERIFY_SSL_CERT = False
        libcloud.security.CA_CERTS_PATH = ['/home/tmp/PycharmProjects/untitled2/powervc.crt']

        # The API endpoint returns host 'powervc', which is unknown to the FSOC DNS
        # Add to /etc/hosts: 192.168.42.252 powervc
        # OR use ex_force_base_url: https://192.168.42.252:8774/v2.1

        self._cfg = cfg
        self._conn = OpenStackNodeDriver(cfg['auth']['username'],
                                         cfg['auth']['password'],
                                         ex_tenant_name=cfg['auth']['tenant_name'],
                                         ex_force_auth_url=cfg['auth']['url'],
                                         # ex_force_base_url=cfg['auth']['base_url'],
                                         ex_force_auth_version=cfg['auth']['version'],
                                         ex_force_service_region=cfg['auth']['region_name'])

        self.id = self._cfg['id']
        self.availability = self._cfg['availability']
        self.cost = self._cfg['cost']
        self.location = self._cfg['location']['country']

        from pprint import pprint

        name = 'testing2'
        # command = ' '.join(template['provider']['docker']['command']))

        cloud_init_ubuntu_passwort = """
            #cloud-config
            
            chpasswd:
              list: |
                ubuntu:password
              expire: False            
            """

        cloud_init_hyrise_r_dispatcher = """
            #cloud-config
            
            runcmd:
                - cd /home/ubuntu/hyrise_dispatcher/dispatcher
                - ./start_dispatcher 8888 settings.json
            """

        cloud_init_hyrise_r_master = """
            #cloud-config

            runcmd:
                - cd /home/ubuntu/hyrise/hyrise_nvm/build
                - ./hyrise-server_release --corecount=2 --dispatcherurl=10.6.0.26 --dispatcherport=8888 --port=8889 --nodeId=0
            """

        # Nodes are tagged with metadata, to reconstruct running app instances after CMP cold boot
        # state=RUNNING, manually assign a floating ip or wait and call until private ip is available.

        # creating a new floating ip is necessary for the scheduler's deployment plan

        # Clean up!

        pprint(self.nodes)

    def clean_test_setup(self):
        """Remove all deployed Instances"""
        self._destroy_all_instances()

    def request_ip(self):
        """Get the Next (Unused) Floating IP"""
        unused_floating_ip = None
        for floating_ip in self._conn.ex_list_floating_ips():
            if not floating_ip.node_id:
                unused_floating_ip = floating_ip.ip_address
                break
        return unused_floating_ip or self._conn.ex_create_floating_ip().ip_address

    def request_port(self):
        """Get the Next Free Port
            In OpenStack there is no limitation here, as each instance is an individual VM."""
        return 8888

    @property
    def provider(self):
        """Get Cloud Provider ID"""
        return self._conn.type

    @property
    def images(self):
        """List Images"""
        return self._conn.list_images()

    @property
    def sizes(self):
        """List Sizes"""
        # PowerVC lists more options here than on the Web Interface
        return self._conn.list_sizes()

    @property
    def nodes(self):
        """List Nodes"""
        # Node data misses the ip address.
        # Check Hardware Management Console (HMT) at 192.168.42.251
        return self._conn.list_nodes()

    @traced()
    def _destroy_all_instances(self, stopped=True):
        """Stop and Remove all Containers"""
        # We use dummy.Pool for a simpler threading interface,
        # as we wait for net i/o instead of a calculation,
        # which would actually need multiprocessing.
        with Pool(8) as pool:
            with ignored(Exception):
                pool.map(lambda n: n.stop(), self.nodes)
            with ignored(Exception):
                pool.map(lambda n: n.destroy(), self.nodes)

    def deploy_template(self, name, template, run_config):
        """Extract Service Instance Data from Template"""
        return self.deploy(
            name,
            image=self._get_image(template['provider']['openstack']['image']),
            size=self._get_size('m1.large'),
            command=template['provider']['openstack']['command'],
            ip=run_config['ip'],
            labels={},
        )

    def deploy(self, name, image, size,
               command=None, network=None, ip=None, labels=None, remove_existing=False):
        """Deploy Service Instance"""
        existing_instance = self._get_node(name)
        if remove_existing and existing_instance:
            existing_instance.destroy()
        if network is None:
            network = self._get_network('admin_internal_net')

        return self._deploy_instance(name, size, image, network, command, ip, labels)

    @traced()
    def _deploy_instance(self, name, size, image, network, command=None, ip=None, labels=None):
        """Create Instance"""

        # libcloud expects a label dictionary, even if empty
        if labels is None:
            labels = {}

        new_instance = self._conn.create_node(name=name, image=image, size=size, networks=[network],
                                              ex_userdata=command, ex_metadata=labels)

        if ip:
            # A floating ip can only be associated to a running instance,
            # so we wait for spawning to complete
            self._conn.wait_until_running([new_instance])
            self._conn.ex_attach_floating_ip_to_node(new_instance, ip)

        return new_instance

    def _get_node(self, name):
        """Get Node by Name"""
        # root:power8
        return next((n for n in self.nodes if n.name == name), None)

    def _get_image(self, name):
        """Get Image by Name"""
        existing_image = next((i for i in self.images if i.name == name), None)
        return existing_image  # or self._install_image(path)

    @traced('name')
    def _container_log(self, node):
        """Get Docker Container Logs"""
        return self._conn.ex_get_console_output(node)

    @property
    def _networks(self):
        """List Networks"""
        return self._conn.ex_list_networks()

    def _get_network(self, name):
        """Get Network by Name"""
        return next((n for n in self._networks if n.name == name), None)
    #
    # def _get_ip(self, ip_str):
    #     return self._conn.ex_get_floating_ip(ip_str)

    def _get_size(self, name=None, core_count=None, core_mhz=None, ram_mb=None, disk_mb=None):
        """Get Size by Name or TODO: Resources"""
        return next((s for s in self.sizes if s.name == name), None)
