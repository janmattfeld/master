import multiprocessing.dummy
import functools

import libcloud.container.drivers.docker
import libcloud.container.providers

import utils
from log import traced, ignored


class Cloud:
    """
    # Docker
    #
    # How-to setup Docker API access on host
    # https://stackoverflow.com/documentation/docker/3935/docker-engine-api#t=201707221117108881869
    #
    # Instead of None, we need to pass empty strings for key and secret, apache/libcloud/pull/1067
    """

    @traced('text')
    def __init__(self, cfg):
        """Initialize Cloud"""
        self._id = utils.create_uuid()
        self._cfg = cfg
        self._drv = libcloud.container.providers.get_driver(cfg['provider'])
        self._conn = self._drv(key="",
                               secret="",
                               host=cfg['auth']['host'],
                               port=cfg['auth']['port'])
        self._containers = self._list_containers(state='all')
        self._images = self._list_images('all')

        # We start in a clean cloud environment
        self._destroy_all_containers()

    def _refreshed(func):
        """
        Get list of Containers and Images

        This wrapper may be used on all infrastructure-changing methods,
        which create, start, stop or destroy containers and images.

        TODO: Use a contextmanager instead of class-method-decorator-hack
        TODO: Do we want to keep a state at all?
        """

        @functools.wraps(func)
        def decorated_function(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            # self._containers = self._list_containers(state='all')
            # self._images = self._list_images('all')
            return result

        return decorated_function

    @_refreshed
    @traced()
    def _deploy_container(self, name, image, command, labels=None):
        """Deploy Container"""
        return self._conn.deploy_container(name,
                                           image=self.get_image(image),
                                           command=command,
                                           network_mode='host')

    @_refreshed
    @traced('name')
    def _start_container(self, container):
        """Start Container"""
        return self._conn.start_container(container)

    @_refreshed
    @traced('name')
    def _stop_container(self, container):
        """Stop Container"""
        with ignored(Exception):
            return self._conn.stop_container(container)

    @_refreshed
    @traced('name')
    def _remove_container(self, container):
        """Remove Container"""
        with ignored(Exception):
            return self._conn.destroy_container(container)

    @traced('name')
    def _container_log(self, container):
        """Get Container Logs"""
        return self._conn.ex_get_logs(container)

    def _list_containers(self, state='all'):
        """List Containers"""
        return self._conn.list_containers(all=True if state == 'all' else False)

    @_refreshed
    @traced()
    def _destroy_all_containers(self, stopped=True):
        """Stop and Remove all Containers"""
        # We use dummy.Pool for a simpler threading interface,
        # as we wait for net i/o instead of a calculation,
        # which would actually need multiprocessing.
        with multiprocessing.dummy.Pool(32) as pool:
            pool.map(self._stop_container, self._list_containers())
        with multiprocessing.dummy.Pool(32) as pool:
            pool.map(self._remove_container, self._list_containers())

    def _list_images(self, filter='all'):
        """List Images"""
        return self._conn.list_images()

    @_refreshed
    @traced()
    def _install_image(self, path):
        """Install Image"""
        return self._conn.install_image(path)

    def deploy_template(self, name, template):
        return self.deploy(
            name,
            template['docker']['image'],
            ' '.join(template['docker']['command']))

    def deploy(self, name, image, command, labels=[], remove_existing=True):
        """Deploy Service Instance"""
        existing_container = self.get_container(name)
        if remove_existing and existing_container:
            self._remove_container(existing_container)
        return self._deploy_container(name, image, command, labels)

    def get_image(self, path):
        """Get Image by Path"""
        existing_image = next((i for i in self._images if i.path == path), None)
        return existing_image or self._install_image(path)

    def get_images(self, path):
        """Get All Images"""
        return self._images

    def get_container(self, name):
        """Get Container by Name"""
        return next((c for c in self._containers if c.name == name), None)

    def get_containers(self):
        """Get All Containers"""
        return self._containers

    def get_availability(self):
        """Get Hardware Location"""
        return self._cfg['get_availability']

    def get_cost(self):
        """Get Basic Computing Costs"""
        return self._cfg['cost']

    def get_country(self):
        """Get Cloud Location"""
        return self._cfg['location']['country']

# OpenStack
# from libcloud.compute.providers import get_driver as compute_get_driver
# from libcloud.compute.types import Provider as compute_provider
#
# USER_NAME = 'admin'
# PASSWORD = 'secret'
# TENANT_NAME = 'admin'
# AUTH_URL = 'http://172.20.5.51/identity'
# region_name = 'RegionOne'
#
# driver = compute_get_driver(compute_provider.OPENSTACK)(
#     USER_NAME, PASSWORD, ex_tenant_name=TENANT_NAME,
#     ex_force_auth_url="http://172.20.5.51/identity/v2.0/tokens",
#     ex_force_auth_version='2.0_password',
#     ex_force_service_region=region_name)
#
# logging.info(driver.list_images())
