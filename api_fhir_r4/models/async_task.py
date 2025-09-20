import uuid
from django.db import models
from django.utils import timezone
from enum import Enum


class TaskStatus(Enum):
    """Task status codes as per FHIR R4 specification"""
    DRAFT = "draft"
    REQUESTED = "requested"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    READY = "ready"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in-progress"
    ON_HOLD = "on-hold"
    FAILED = "failed"
    COMPLETED = "completed"
    ENTERED_IN_ERROR = "entered-in-error"


class AsyncTask(models.Model):
    """Model to track asynchronous FHIR operations"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resource_type = models.CharField(max_length=100, help_text="FHIR resource type (e.g., ActivityDefinition)")
    operation = models.CharField(max_length=50, help_text="Operation type (e.g., read, search)")
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in TaskStatus],
        default=TaskStatus.REQUESTED.value
    )
    request_data = models.JSONField(null=True, blank=True, help_text="Original request data")
    result_data = models.JSONField(null=True, blank=True, help_text="Result data when completed")
    error_message = models.TextField(null=True, blank=True, help_text="Error message if failed")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'api_fhir_r4_async_task'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.resource_type} {self.operation} - {self.status} ({self.id})"
    
    def mark_as_in_progress(self):
        """Mark task as in progress"""
        self.status = TaskStatus.IN_PROGRESS.value
        self.save()
    
    def mark_as_completed(self, result_data=None):
        """Mark task as completed with optional result data"""
        self.status = TaskStatus.COMPLETED.value
        self.completed_at = timezone.now()
        if result_data:
            self.result_data = result_data
        self.save()
    
    def mark_as_failed(self, error_message):
        """Mark task as failed with error message"""
        self.status = TaskStatus.FAILED.value
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save()
    
    def mark_as_cancelled(self):
        """Mark task as cancelled"""
        self.status = TaskStatus.CANCELLED.value
        self.completed_at = timezone.now()
        self.save()
