from celery import shared_task
from .services.git_manager import Repository
from .models import Project

@shared_task
def clone_and_build_project(project_id):

    """Asynchronously clones a project's repository and compiles its documentation.

    Args:
        project_id (_type_): The primary key (ID) of the Project record in the database.

    Returns:
        str: A success message containing the name of the built project.
    """

    project = Project.objects.get(id=project_id)
    
    repo = Repository(project.repo)
    repo.clone(project.get_absolute_path())

    project.import_documents()
    
    return f"Successfully built {project.name}"