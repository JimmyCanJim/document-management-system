from celery import shared_task
import logging
from .services.git_manager import Repository
from .models import Project
from .services.sphinx_compiler import SphinxCompiler

logger = logging.getLogger(__name__)

@shared_task
def clone_and_build_project(project_id):

    """Asynchronously clones a project's repository and compiles its documentation.
    This is only triggered the first time a project is cloned.

    Args:
        project_id (int): The primary key (ID) of the Project record in the database.

    Returns:
        str: A success message containing the name of the built project.
    """

    try: 
        project = Project.objects.get(project_id)
        local_path = project.get_absolute_path()

        repo = Repository(repo_url=project.repo, local_path=local_path)

        if not repo.clone():
            logger.error(f"Task Aborted: Could not clone {project.name}")
            return f"Failed to clone {project.name}"
        
        compiler = SphinxCompiler(
            source_dir=local_path / project.source,
            build_dir=local_path / project.target
        )

        if not compiler.build():
            logger.error(f"Task Aborted: Sphinx build failed for {project.name}")
            return f"Failed to compile {project.name}"
        
        project.import_documents()

        logger.info(f"Task Complete: {project.name} is live.")
        return f"Successfully built {project.name}"
    
    except Project.DoesNotExist:
        error_message = f"Task Aborted: Project ID {project_id} does not exist."
        logger.error(error_message)
        return error_message
        
    except Exception as e:
        error_message = f"Task Crashed: Unexpected error building Project {project_id}: {str(e)}"
        logger.error(error_message)
        return error_message
    

@shared_task
def pull_and_update_project(project_id):
    """Asynchronously updates and pulls the new updated project.
    Triggered by GitHub Webhooks when new code is pushed.

    Args:
        project_id (int): The primary key (ID) of the Project record in the database.

    Returns:
        str: A success message containing the name of the built project.
    """
    try:
        project = Project.objects.get(project_id)
        local_path = project.get_absolute_path()

        repo = Repository(repo_url = project.repo, local_path=local_path)

        if not repo.pull():
            return f"Failed to pull updates for {project.name}"
        
        compiler = SphinxCompiler(
            source_dir=local_path / project.source,
            build_dir= local_path / project.target
        )

        if not compiler.build():
            return f"Failed to compile {project.name}"
        
        project.import_documents()
        return f"Successfully updated {project.name}"

    except Exception as e:
        error_message = f"Task Crashed: Unexpected error updating Project {project_id}: {str(e)}"
        logger.error(error_message)
        return error_message
