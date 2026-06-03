import subprocess
import logging
import os
import re
from pathlib import Path
from urllib.parse import urlparse
from django.conf import settings

logger = logging.getLogger(__name__)

class Repository:

    """Git repository management utility class.

    This service class wraps standard Git terminal commands using Python's 
    subprocess module. It is designed to be executed by asynchronous Celery 
    workers to clone and update documentation repositories securely.
    """
    
    def __init__(self, repo_url, local_path, branch=None, timeout=300):

        """Initializes the Git repository manager.
        
        Args:
            repo_url (str): The Git repository URL (HTTPS or SSH).
            local_path (str | Path): The absolute local directory path on the server.
            branch (str, optional): The specific branch to target. Defaults to None (main/master).
            timeout (int, optional): Maximum execution time in seconds. Defaults to 300.
        """

        self.repo = repo_url
        self.path = Path(local_path)
        self.branch = branch
        self.timeout = timeout        
        self.credentials = getattr(settings, "VERSION_CONTROL_CREDENTIALS", {}).get("git", {})


    @property
    def is_ssh(self):
        """Determines if the repository uses SSH authentication."""
        return self.repo.startswith('git@') or self.repo.startswith('ssh://')


    @property
    def secure_repository_url(self):
        """Injects authentication tokens into HTTP(S) URLs if required.
        
        Returns:
            str: The raw SSH URL, or the HTTP(S) URL embedded with a personal access token.
        """
        if self.is_ssh:
            return self.repo

        parsed_url = urlparse(self.repo)
        token = self.credentials.get(parsed_url.hostname)
        
        if token and parsed_url.scheme in ('http', 'https'):
            # Formats: https://:TOKEN@github.com/user/repo.git
            return f"{parsed_url.scheme}://:{token}@{parsed_url.netloc}{parsed_url.path}"
        
        return self.repo


    @property
    def environment(self):
        """Prepares a safe copy of the system environment for Git operations.
        
        Injects specific SSH key paths if required by the Django settings, 
        bypassing strict host key checking for automated background tasks.
        
        Returns:
            dict: The modified environment variables.
        """
        env = os.environ.copy()
        
        if self.is_ssh:
            ssh_key = getattr(settings, 'SPHINXDOC_SSH_KEY_PATH', None)
            if ssh_key:
                env['GIT_SSH_COMMAND'] = f'ssh -i {ssh_key} -o StrictHostKeyChecking=no'
    
        return env


    @property
    def is_cloned(self):
        """Checks if the repository currently exists on the local disk."""
        return self.path.exists() and (self.path / '.git').exists() and (self.path / '.git').is_dir()


    def clone(self):

        """Clones the repository from the remote server to the local disk.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        
        if self.is_cloned:
            logger.info(f"Repository already exists at {self.path}")
            return True
            
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            cmd = ['git', 'clone', '--recurse-submodules']            
            
            if self.branch:
                cmd.extend(['--branch', self.branch, '--single-branch'])            
                
            cmd.extend([self.secure_repository_url, str(self.path)])
            
            logger.info(f"Executing Clone Operation for {self.repo}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=self.environment,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully cloned to {self.path}")
                return True
            else:
                logger.error(f"Failed to clone {self.repo}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Clone operation timed out after {self.timeout} seconds for {self.repo}")
            return False
        except Exception as e:
            logger.error(f"System error cloning repository {self.repo}: {str(e)}")
            return False


    def pull(self):
        """Pulls the latest commits from the remote repository.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.is_cloned:
            logger.error("Cannot pull: Repository is not cloned locally.")
            return False        
            
        try:
            cmd = ['git', 'pull', 'origin']
            cmd.append(self.branch if self.branch else 'HEAD')
            
            result = subprocess.run(
                cmd,
                cwd=str(self.path),
                capture_output=True,
                text=True,
                env=self.environment,
                timeout=self.timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully pulled latest changes to {self.path}")
                return True
            else:
                logger.error(f"Failed to pull {self.repo}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Pull operation timed out after {self.timeout} seconds.")
            return False
        except Exception as e:
            logger.error(f"System error pulling repository {self.repo}: {str(e)}")
            return False