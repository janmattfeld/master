import jinja2
import ruamel.yaml as yaml

import utils
import scheduler


class Template:
    """Jinja2 dict/YAML template for app deployment"""

    def __init__(self, name, template):
        self.id = name
        self._template = template
        self._path = './deployments/{id}.yaml'.format(id=self.id)

        self.__save_yaml()
        self.update({'app_id': self.id})

    def __get__(self, instance, owner):
        return self._template

    def __getitem__(self, item):
        return self._template[item]

    def __repr__(self):
        return self._template

    def __save_yaml(self, path=None):
        """Persist template to disk as YAML"""
        with open(path or self._path, 'w') as f:
            yaml.YAML().dump(self._template, f)

    def update(self, value=None, persist=True):
        """Update Template"""
        if value is None:
            value = {}

        class IgnoreMissingAttribute(jinja2.DebugUndefined):
            """Preserve placeholders, ignore missing objects or attributes"""

            def __getattr__(self, name):
                return u'{{ %s.%s }}' % (self._undefined_name, name)

        # Load and update the last saved yaml as new template
        env = jinja2.Environment(loader=jinja2.FileSystemLoader('.'), undefined=IgnoreMissingAttribute)
        template = env.get_template(self._path)
        updated_template = yaml.YAML().load(template.render(value))

        if persist:
            self._template = updated_template
            self.__save_yaml()

        return updated_template


class App:
    #
    # Apps consist of a global dispatcher, 0..1 master and 0..n replica nodes.
    # These are described in a Service Template (YAML).
    #
    # Constraints during deployment planning:
    #  - Service Dependencies -> Handled here
    #  - Hard Constraints (Hardware, Features) -> Scheduler
    #  - Soft Constraints (Availability, Performance, Price) -> Scheduler
    #
    # Constraints during runtime:
    #  - Service Dependencies -> Handled here
    #  - Overall Performance -> Handled here
    #  - Hard Constraints (Hardware, Features) -> Scheduler
    #  - Soft Constraints (Availability, Performance, Price) -> Scheduler
    #
    def __init__(self, template, sla, clouds):
        self.id = utils.create_uuid(template['name'])
        self._template = Template(self.id, template)
        self._sla = sla
        self._clouds = clouds
        self._services = []
        self._deploy_services()

    # def __del__(self):
    #     """Remove all of the app's service instances"""
    #     del self._services[:]

    # TODO: Checks at App-level
    # 0. Are all deployed instances still alive?
    #    a) Reconstruct Template from running instance information (labels)
    # 1. Measure Throughput, Response Time
    # 2. Change Template, if needed
    # 3. Re-run _deploy_services()

    def _get_service_by_role(self, role):
        """Return ONE service of a given role"""
        return next((srv for srv in self._services if srv.role == role), None)

    def _get_services_by_role(self, role):
        """Return ALL services of a given role"""
        return [srv for srv in self._services if srv.role == role]

    def _deploy_services(self):

        _queued_services = self._template['services']

        def _is_global():
            """Only one instance of this service shall exist within a cluster"""
            return srv['deploy']['mode'] == 'global'

        def _is_replicated():
            """Replication requirement satisfied for this role"""
            return len(self._get_services_by_role(srv['role'])) >= srv['deploy']['replicas']

        def _role_is_deployed():
            """A required number of this role's services already exists"""
            return _is_global() and self._get_service_by_role(srv['role']) or not _is_global() and _is_replicated()

        def _dependencies_fulfilled():
            """All required services exist"""
            is_fulfilled = True
            for dep in srv['depends_on']:
                if dep != 'None' and not self._get_service_by_role(dep):
                    is_fulfilled = False
            return is_fulfilled

        while _queued_services:
            for srv in _queued_services:
                while not _role_is_deployed() and _dependencies_fulfilled():

                    # Ask scheduler for a suitable cloud
                    scheduled_cloud = scheduler.place(self._clouds, srv, self._sla)
                    # TODO Fail if None

                    scheduled_port = scheduled_cloud.request_port()
                    run_config = {
                        'ip': scheduled_cloud.request_ip(),
                        'port': scheduled_port,
                        'id': scheduled_port
                    }

                    # We have to update the service template before deploying (--ip and --port)
                    # Without Consul/ZooKeeper, the included app may depend on this IP/Port information
                    # A non-global service will be changed again, so there is no need to persist it
                    updated_app_template = self._template.update({srv['role']: run_config}, persist=_is_global())

                    # Get updated template for this service
                    srv_template = next((s for s in updated_app_template['services'] if s['role'] == srv['role']), None)

                    self._services.append(Service(srv_template, scheduled_cloud, run_config))

                    if _role_is_deployed():
                        _queued_services.remove(srv)

    def __repr__(self):
        return "<{name}: id={id}>".format(name=__name__, id=self.id)


class Service:
    """A service instance is deployed within a scheduled cloud, according to its template"""

    def __init__(self, template, cloud, run_config):
        self.id = utils.create_uuid(template['role'])
        self._role = template['role']
        self._cloud = cloud
        self._template = template
        self._run_config = run_config
        self._instance = cloud.deploy_template(self.id, template, run_config)

    # def __del__(self):
    #     self._instance.destroy()

    @property
    def role(self):
        return self._role

    @property
    def port(self):
        # TODO get this dynamically (impossible for docker)
        # That is why we really need something like Consul/Zookeeper
        return self._run_config['port']

    @property
    def ip(self):
        # TODO get this dynamically (impossible for docker)
        return self._run_config['ip']

    def __repr__(self):
        return "<{name}: id={id}>".format(name=__name__, id=self.id)
