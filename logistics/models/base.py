from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    """Abstract base with primary key, audit timestamps, and user tracking."""

    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_created',
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class)s_updated',
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def apply_audit_user(self, user):
        if self._state.adding and not self.created_by_id:
            self.created_by = user
        self.updated_by = user
