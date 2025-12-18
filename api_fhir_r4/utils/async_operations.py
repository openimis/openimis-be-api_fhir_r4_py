import json
import threading
from typing import Dict, Any, Optional
from django.http import JsonResponse
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from api_fhir_r4.models.async_task import AsyncTask, TaskStatus


def create_operation_outcome_with_task_id(task_id: str, message: str = None, base_url: str = None) -> Dict[str, Any]:
    """
    Create an OperationOutcome resource with task ID as per FHIR R4 specification.
    
    Args:
        task_id: The unique task identifier
        message: Optional custom message
        base_url: Base URL for the API (optional)
    
    Returns:
        Dict representing OperationOutcome resource
    """
    if message is None:
        message = f"Request accepted for asynchronous processing. Use request ID '{task_id}' to check status."
    
    # Default to localhost if base_url not provided
    if base_url is None:
        base_url = "http://127.0.0.1:8000"
    
    return {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "information",
                "code": "informational",
                "details": {
                    "text": message
                },
                "expression": [
                    f"{base_url}/api/fhir_R4_ActivityDefinition/ActivityDefinition/async-result/{task_id}/"
                ]
            }
        ]
    }


def create_task_status_response(task: AsyncTask) -> Dict[str, Any]:
    """
    Create a Task resource response for status checking.
    
    Args:
        task: The AsyncTask instance
    
    Returns:
        Dict representing Task resource
    """
    task_resource = {
        "resourceType": "Task",
        "id": str(task.id),
        "status": task.status,
        "intent": "order",
        "priority": "routine",
        "code": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/task-code",
                    "code": "fulfill",
                    "display": "Fulfill the focal request"
                }
            ]
        },
        "description": f"{task.resource_type} {task.operation}",
        "created": task.created_at.isoformat(),
        "lastModified": task.updated_at.isoformat()
    }
    
    if task.completed_at:
        task_resource["executionPeriod"] = {
            "start": task.created_at.isoformat(),
            "end": task.completed_at.isoformat()
        }
    
    if task.status == TaskStatus.COMPLETED.value and task.result_data:
        task_resource["output"] = [
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/CodeSystem/task-output-type",
                            "code": "result",
                            "display": "Result"
                        }
                    ]
                },
                "valueReference": {
                    "reference": f"{task.resource_type}/{task.result_data.get('id', 'unknown')}"
                }
            }
        ]
    
    if task.status == TaskStatus.FAILED.value and task.error_message:
        task_resource["statusReason"] = {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/task-failure-reason",
                    "code": "error",
                    "display": "Error"
                }
            ],
            "text": task.error_message
        }
    
    return task_resource


def create_async_response(task_id: str, message: str = None, base_url: str = None) -> JsonResponse:
    """
    Create a JSON response with OperationOutcome containing task ID.
    
    Args:
        task_id: The unique task identifier
        message: Optional custom message
        base_url: Base URL for the API (optional)
    
    Returns:
        JsonResponse with OperationOutcome
    """
    operation_outcome = create_operation_outcome_with_task_id(task_id, message, base_url)
    return JsonResponse(operation_outcome, status=202)  # 202 Accepted


def execute_async_task(task_id: str, operation_func, *args, **kwargs):
    """
    Execute an async task in a separate thread.
    
    Args:
        task_id: The unique task identifier
        operation_func: Function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
    """
    def run_task():
        try:
            task = AsyncTask.objects.get(id=task_id)
            task.mark_as_in_progress()
            
            # Execute the actual operation
            result = operation_func(*args, **kwargs)
            
            # Serialize result to handle Decimal and other non-JSON-serializable types
            if result is not None:
                try:
                    # Convert to JSON and back to ensure proper serialization
                    serialized_result = json.loads(json.dumps(result, cls=DjangoJSONEncoder))
                except (TypeError, ValueError):
                    # If serialization fails, convert to string
                    serialized_result = str(result)
            else:
                serialized_result = None
            
            # Mark as completed with result
            task.mark_as_completed(serialized_result)
            
        except Exception as e:
            try:
                task = AsyncTask.objects.get(id=task_id)
                task.mark_as_failed(str(e))
            except AsyncTask.DoesNotExist:
                pass  # Task might have been deleted
    
    # Start the task in a separate thread
    thread = threading.Thread(target=run_task)
    thread.daemon = True
    thread.start()


def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of an async task.
    
    Args:
        task_id: The unique task identifier
    
    Returns:
        Dict representing Task resource or None if not found
    """
    try:
        task = AsyncTask.objects.get(id=task_id)
        return create_task_status_response(task)
    except AsyncTask.DoesNotExist:
        return None


def get_task_result(task_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the result of a completed async task.
    
    Args:
        task_id: The unique task identifier
    
    Returns:
        Dict containing the result data or None if not found/completed
    """
    try:
        task = AsyncTask.objects.get(id=task_id)
        if task.status == TaskStatus.COMPLETED.value and task.result_data:
            return task.result_data
        return None
    except AsyncTask.DoesNotExist:
        return None
