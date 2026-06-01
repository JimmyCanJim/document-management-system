from celery import shared_task
from .services.git_manager import Repository
from .models import Project

@shared_task
def clone_and_build_project(project_id):
    project = Project.objects.get(id=project_id)
    
    repo = Repository(project.repo)
    repo.clone(project.get_absolute_path())

    project.import_documents()
    
    return f"Successfully built {project.name}"