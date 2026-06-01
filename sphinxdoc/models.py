import os
import json
from pathlib import Path
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
# Import PostgreSQL specific fields for native search
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex

from sphinxdoc.validators import validate_relative_path

class Project(models.Model):
    """Represents a Sphinx project repository and configuration."""
    
    name = models.CharField(_("project"), max_length=100)
    slug = models.SlugField(unique=True, blank=True, max_length=100)
    repo = models.URLField(_("repository"), max_length=255, blank=True)
    
    root = models.CharField(
        max_length=255, 
        blank=True,
        validators=[validate_relative_path],
        help_text=_("Project's root directory")
    )
    source = models.CharField(
        max_length=255, 
        default="docs", 
        blank=True,
        validators=[validate_relative_path],
        help_text=_("Relative path containing RST and conf.py")
    )
    target = models.CharField(
        max_length=255, 
        default="_build",
        validators=[validate_relative_path],
        help_text=_("Relative path containing Sphinx output")
    )
    
    created = models.DateTimeField(auto_now_add=True)
    deleted = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug and root paths cleanly before saving."""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if not self.root:
            self.root = self.slug
            
        super().save(*args, **kwargs)

    def get_absolute_path(self):
        """Helper to get the full absolute path on the file system."""
        base_dir = getattr(settings, 'MEDIA_ROOT', settings.BASE_DIR / 'media')
        return Path(base_dir) / 'repos' / self.root

    def import_documents(self):
        """Crawls the built Sphinx JSON and updates the PostgreSQL database."""
        SPECIAL_TITLES = {
            'genindex': 'General Index',
            'py-modindex': 'Module Index',
            'np-modindex': 'Module Index',
            'search': 'Search',
        }
        
        # Target the json directory created by Sphinx
        target_dir = self.get_absolute_path() / self.target / 'json'
        
        if not target_dir.exists():
            raise FileNotFoundError(f"JSON build directory not found at {target_dir}")

        # Clear old documents before importing
        self.documents.all().delete()

        documents_to_create = []

        for dirpath, _, filenames in os.walk(target_dir):
            for filename in [f for f in filenames if f.endswith('.fjson')]:
                filepath = Path(dirpath) / filename
                relpath = str(filepath.relative_to(target_dir))[:-6] # Remove .fjson

                with open(filepath, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)

                # Resolve title
                title = doc_data.get('title') or doc_data.get('indextitle')
                if not title:
                    page_name = Path(relpath).name
                    title = SPECIAL_TITLES.get(page_name, page_name)

                documents_to_create.append(
                    Document(
                        project=self,
                        path=relpath,
                        title=title,
                        body=doc_data.get('body', ''),
                        content=json.dumps(doc_data)
                    )
                )

        # Bulk create is significantly faster than saving one by one
        if documents_to_create:
            Document.objects.bulk_create(documents_to_create)
            
            # Now trigger the Postgres Search Vector update
            Document.objects.filter(project=self).update(
                search_vector=SearchVector('title', weight='A') + SearchVector('body', weight='B')
            )

class Document(models.Model):
    """Represents a compiled document with full-text search indexing."""
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    content = models.TextField(_("JSON data structure"))
    
    # The dedicated PostgreSQL search engine field
    search_vector = SearchVectorField(null=True)

    class Meta:
        verbose_name = _('document')
        verbose_name_plural = _('documents')
        indexes = [
            # Creates an ultra-fast Generalized Inverted Index (GIN) in Postgres
            GinIndex(fields=['search_vector']),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.title}"

    def get_absolute_url(self):
        return reverse('doc-detail', kwargs={'slug': self.project.slug, 'path': self.path})