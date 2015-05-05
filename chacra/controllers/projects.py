from pecan import expose, abort, request
from chacra.models import projects, Distro, DistroVersion, DistroArch, Binary, commit
from chacra import models
from chacra.controllers import error


# TODO: move this out of here
def set_id_in_context(name, object_model, value):
    # if the object_model is None, then it will save it as None
    # saving us from having to do this everywhere
    object_name = name.split('_id')[0]
    if object_model is not None:
        request.context[name] = object_model.id
        request.context[object_name] = object_model.name
    else:
        request.context[name] = None
        request.context[object_name] = value


class BinaryController(object):

    def __init__(self, binary_name):
        self.binary_name = binary_name
        self.binary = Binary.query.filter_by(name=binary_name).first()
        if not self.binary and request.method != 'POST':
                abort(404)

    @expose('json', generic=True)
    def index(self):
        # TODO: implement downloads
        return dict(name=self.binary.name)

    @index.when(method='POST', template='json')
    def index_post(self):
        # updates the binary
        return
        try:
            data = request.json
            name = data.get('name')
        except ValueError:
            error('/errors/invalid/', 'could not decode JSON body')
        # we allow empty data to be pushed
        if not name:
            error('/errors/invalid/', "could not find required key: 'name'")
        self.ensure_objects(name)
        return True

    def ensure_objects(self, binary_name):
        """
        Since we might not have everything created, ensure everything is
        and push it to the database
        """
        project_id = request.context.get('project_id')
        distro_id = request.context.get('distro_id')
        version_id = request.context.get('version_id')
        arch_id = request.context.get('distro_arch_id')
        is_none = lambda x: x is None
        if all(
                [is_none(i) for i in [project_id, distro_id, version_id, arch_id]]):
            project = projects.Project(request.context['project'])
            distro = Distro(request.context['distro'], project)
            version = DistroVersion(request.context['version'], distro)
            arch = DistroArch(request.context['distro_arch'], version)
            models.flush()
            models.commit()
            binary = Binary(binary_name, arch)
            return binary


class ArchController(object):

    def __init__(self, arch_name):
        self.arch_name = arch_name
        self.distro_arch = DistroArch.query.filter_by(name=arch_name).first()
        if not self.distro_arch and request.method != 'POST':
            abort(404)
        set_id_in_context('distro_arch_id', self.distro_arch, arch_name)

    @expose(generic=True, template='json')
    def index(self):
        return dict(
            (d.name, d) for d in self.distro_arch.binaries.all()
        )

    @index.when(method='POST', template='json')
    def index_post(self):
        # updates the binary
        try:
            data = request.json
            name = data.get('name')
        except ValueError:
            error('/errors/invalid/', 'could not decode JSON body')
        # we allow empty data to be pushed
        if not name:
            error('/errors/invalid/', "could not find required key: 'name'")
        self.ensure_objects(name)
        return True

    def ensure_objects(self, binary_name):
        """
        Since we might not have everything created, ensure everything is
        and push it to the database
        """
        project_id = request.context.get('project_id')
        distro_id = request.context.get('distro_id')
        version_id = request.context.get('distro_version_id')
        arch_id = request.context.get('distro_arch_id')
        is_none = lambda x: x is None
        print request.context
        if all(
                [is_none(i) for i in [project_id, distro_id, version_id, arch_id]]):
            project = projects.Project(request.context['project'])
            distro = Distro(request.context['distro'], project)
            version = DistroVersion(request.context['distro_version'], distro)
            arch = DistroArch(request.context['distro_arch'], version)
            models.flush()
            models.commit()
            binary = Binary(binary_name, arch)
            return binary

    @expose()
    def _lookup(self, name, *remainder):
        return BinaryController(name), remainder


class DistroVersionController(object):

    def __init__(self, version_name):
        self.version_name = version_name
        self.distro_version = DistroVersion.query.filter_by(name=version_name).first()
        if not self.distro_version and request.method != 'POST':
            abort(404)
        set_id_in_context('distro_version_id', self.distro_version, version_name)

    @expose('json')
    def index(self):
        return dict(
            (d.name, d) for d in self.distro_version.archs.all()
        )

    @expose()
    def _lookup(self, name, *remainder):
        return ArchController(name), remainder


class DistroController(object):
    def __init__(self, distro_name):
        self.distro_name = distro_name
        self.distro = Distro.query.filter_by(name=distro_name).first()
        if not self.distro and request.method != 'POST':
            abort(404)
        set_id_in_context('distro_id', self.distro, distro_name)

    @expose('json')
    def index(self):
        return dict(
            (d.name, d) for d in self.distro.versions.all()
        )

    @expose()
    def _lookup(self, name, *remainder):
        return DistroVersionController(name), remainder


class ProjectController(object):

    def __init__(self, project_name):
        self.project_name = project_name
        self.project = projects.Project.query.filter_by(name=project_name).first()
        if not self.project and request.method != 'POST':
            abort(404)
        set_id_in_context('project_id', self.project, project_name)

    @expose('json')
    def index(self):
        return dict(
            (d.name, d) for d in self.project.distros.all()
        )

    @expose()
    def _lookup(self, name, *remainder):
        return DistroController(name), remainder


class ProjectsController(object):

    @expose('json')
    def index(self):
        return dict(
            (p.name, p) for p in
            projects.Project.query.all()
        )

    @expose()
    def _lookup(self, project_name, *remainder):
        return ProjectController(project_name), remainder