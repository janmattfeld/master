import jinja2
import ruamel.yaml as yaml

import utils


class Template:
    """Jinja2 dict/YAML template for app deployment"""

    def __init__(self, id, template):
        self._id = id
        self._template = template
        self._path = './deployments/{id}.yaml'.format(id=self._id)

        self.save()
        self.update({'app_id': self._id})

    def save(self, path=None):
        """Persist template to disk as YAML"""
        with open(path or self._path, 'w') as f:
            yaml.YAML().dump(self._template, f)

    def get(self):
        """Return dict representation of template"""
        return self._template

    def update(self, update=None, persist=True):
        """Update template and optionally save it to disk"""

        if update is None:
            update = {}

        class IgnoreMissingAttribute(jinja2.DebugUndefined):
            """Ignores missing objects or attributes, preserving placeholders"""

            def __getattr__(self, name):
                return u'{{ %s.%s }}' % (self._undefined_name, name)

        # Load and update the last saved yaml as new template
        env = jinja2.Environment(loader=jinja2.FileSystemLoader('.'), undefined=IgnoreMissingAttribute)
        template = env.get_template(self._path)
        updated_template = yaml.YAML().load(template.render(update))

        if persist:
            self._template = updated_template
            self.save()

        return updated_template


class App:
    #
    # Apps consist of a global dispatcher, 0..1 master and 0..n replica nodes.
    # These are described in a Service Template.
    #
    # Constraints during deployment planning:
    #  - Service Dependencies -> Handled here
    #  - Hard Constraints (Hardware, Features) -> Scheduler
    #  - Soft Constraints (Availability, Performance, Price) -> Scheduler
    #
    def __init__(self, template, sla, cloud):
        self._id = utils.create_uuid(template['name'])
        self._template = Template(self._id, template)
        self._sla = sla
        self._services = []
        # Not really, should be defined by scheduler
        self._next_free_port = 5099
        self._cloud = cloud
        self._deploy_services()

    def _get_service_by_role(self, role):
        """Returns ONE service of a given role"""
        return next((srv for srv in self._services if srv.get_role() == role), None)

    def _get_services_by_role(self, role):
        """Returns ALL services of a given role"""
        return [srv for srv in self._services if srv.get_role() == role]

    def _deploy_services(self):

        _queued_services = self._template.get()['services']

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

                    run_config = {
                        'ip': '127.0.0.1',
                        'port': self._next_free_port,
                        'id': self._next_free_port
                    }
                    self._next_free_port += 1

                    # we have to update the service template before deploying (--ip and --port)
                    # A non-global service will be changed again, so there is no need to persist it
                    updated_app_template = self._template.update({srv['role']: run_config}, persist=_is_global())

                    # Get updated template for this service
                    srv_template = next((s for s in updated_app_template['services'] if s['role'] == srv['role']), None)

                    self._services.append(Service(srv_template, self._cloud))

                    if _role_is_deployed():
                        _queued_services.remove(srv)


class Service:
    """A service instance is deployed within a scheduled cloud, according to its template"""

    def __init__(self, template, cloud):
        self._id = utils.create_uuid(template['role'])
        self._role = template['role']
        self._cloud = cloud
        self._template = template
        self._instance = cloud.deploy_template(self._id, template)

    def get_role(self):
        return self._role

    def get_port(self):
        pass

    def get_ip(self):
        pass
