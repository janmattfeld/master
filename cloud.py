from multiprocessing.dummy import Pool

from libcloud.container.drivers.docker import DockerContainerDriver
from libcloud.container.drivers.ecs import ElasticContainerDriver
from libcloud.compute.drivers.openstack import OpenStackNodeDriver

from log import traced, ignored


class Cloud:
    @traced('text')
    def __init__(self, cfg):
        """Initialize Cloud"""
        self._cfg = cfg
        self._conn = DockerContainerDriver(key="",
                                           secret="",
                                           host=cfg['auth']['host'],
                                           port=cfg['auth']['port'])
        self.id = self._cfg['id']
        self.availability = self._cfg['availability']
        self.cost = self._cfg['cost']
        self.location = self._cfg['location']['country']

        # We start in a clean cloud environment
        self._destroy_all_containers()

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
            image=template['docker']['image'],
            command=' '.join(template['docker']['command']))

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
        pass
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


        # We start in a clean cloud environment
        # self._destroy_all_containers()


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

        print("asd")
        print(self._conn .list_images())

# OpenStack
#
# DO NOT CREATE VOLUME WHEN DEPLOYING INSTANCE
#
#
