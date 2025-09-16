"""Celery integration for DevPulse."""

import functools
import inspect
import json
import logging
import time
from typing import Any, Callable, Dict, Optional, Union

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure, task_success

from ..core import get_trace_id, set_trace_id

# Setup logger
logger = logging.getLogger("devpulse.integrations.celery")


def _get_task_info(task_id: str, task_name: str, args: tuple, kwargs: dict) -> Dict[str, Any]:
    """Get task information for logging.

    Args:
        task_id: The task ID
        task_name: The task name
        args: The task arguments
        kwargs: The task keyword arguments

    Returns:
        A dictionary with task information
    """
    # Convert args and kwargs to strings
    args_str = []
    for arg in args:
        try:
            args_str.append(str(arg))
        except Exception:
            args_str.append("<not serializable>")

    kwargs_str = {}
    for key, value in kwargs.items():
        try:
            kwargs_str[key] = str(value)
        except Exception:
            kwargs_str[key] = "<not serializable>"

    return {
        "task_id": task_id,
        "task_name": task_name,
        "args": args_str,
        "kwargs": kwargs_str,
    }


def _task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kw):
    """Handle task_prerun signal.

    This function is called before a task is executed. It sets the trace ID
    from the task request or generates a new one if not present.

    Args:
        sender: The task being executed
        task_id: The task ID
        task: The task instance
        args: The task arguments
        kwargs: The task keyword arguments
        **kw: Additional keyword arguments
    """
    # Get trace ID from task request or generate a new one
    trace_id = kwargs.get("trace_id") if kwargs else None
    if not trace_id:
        # Check if trace_id is in task request
        request = getattr(task, "request", None)
        if request:
            trace_id = getattr(request, "trace_id", None)

    # Set trace ID in context
    trace_id = set_trace_id(trace_id)

    # Add trace ID to task request
    if hasattr(task, "request"):
        task.request.trace_id = trace_id

    # Log task start
    task_info = _get_task_info(task_id, task.name, args, kwargs)
    logger.info(
        f"Task started: {task.name}[{task_id}]",
        extra={
            "trace_id": trace_id,
            "system": "celery",
            "task_info": task_info,
            "event_type": "task_start",
        },
    )


def _task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **kw):
    """Handle task_postrun signal.

    This function is called after a task is executed. It logs the task completion
    and the return value.

    Args:
        sender: The task being executed
        task_id: The task ID
        task: The task instance
        args: The task arguments
        kwargs: The task keyword arguments
        retval: The task return value
        **kw: Additional keyword arguments
    """
    # Get trace ID from context
    trace_id = get_trace_id()

    # Convert return value to string
    try:
        retval_str = str(retval)
    except Exception:
        retval_str = "<not serializable>"

    # Log task completion
    task_info = _get_task_info(task_id, task.name, args, kwargs)
    task_info["retval"] = retval_str

    logger.info(
        f"Task completed: {task.name}[{task_id}]",
        extra={
            "trace_id": trace_id,
            "system": "celery",
            "task_info": task_info,
            "event_type": "task_success",
        },
    )


def _task_success_handler(sender=None, result=None, **kw):
    """Handle task_success signal.

    This function is called when a task succeeds. It logs the task success
    and the result.

    Args:
        sender: The task being executed
        result: The task result
        **kw: Additional keyword arguments
    """
    # Get trace ID from context
    trace_id = get_trace_id()

    # Convert result to string
    try:
        result_str = str(result)
    except Exception:
        result_str = "<not serializable>"

    # Log task success
    logger.info(
        f"Task succeeded: {sender.name}[{sender.request.id}]",
        extra={
            "trace_id": trace_id,
            "system": "celery",
            "task_info": {
                "task_id": sender.request.id,
                "task_name": sender.name,
                "result": result_str,
            },
            "event_type": "task_success",
        },
    )


def _task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **kw):
    """Handle task_failure signal.

    This function is called when a task fails. It logs the task failure
    and the exception.

    Args:
        sender: The task being executed
        task_id: The task ID
        exception: The exception that occurred
        args: The task arguments
        kwargs: The task keyword arguments
        traceback: The traceback
        einfo: The exception info
        **kw: Additional keyword arguments
    """
    # Get trace ID from context
    trace_id = get_trace_id()

    # Convert exception to string
    try:
        exception_str = str(exception)
    except Exception:
        exception_str = "<not serializable>"

    # Convert traceback to string
    try:
        traceback_str = str(traceback)
    except Exception:
        traceback_str = "<not serializable>"

    # Log task failure
    task_info = _get_task_info(task_id, sender.name, args, kwargs)
    task_info["exception"] = exception_str
    task_info["traceback"] = traceback_str

    logger.error(
        f"Task failed: {sender.name}[{task_id}] - {exception_str}",
        extra={
            "trace_id": trace_id,
            "system": "celery",
            "task_info": task_info,
            "event_type": "task_failure",
        },
    )


def setup_celery_tracing(app: Celery) -> None:
    """Set up DevPulse tracing for Celery.

    This function connects signal handlers to Celery signals to capture
    task execution details.

    Args:
        app: The Celery application
    """
    # Connect signal handlers
    task_prerun.connect(_task_prerun_handler)
    task_postrun.connect(_task_postrun_handler)
    task_success.connect(_task_success_handler)
    task_failure.connect(_task_failure_handler)

    # Log initialization
    logger.info("DevPulse tracing set up for Celery")


def trace_task(task):
    """Decorator for tracing Celery tasks.

    This decorator adds trace ID propagation to Celery tasks. It extracts
    the trace ID from the task keyword arguments and sets it in the context
    before executing the task.

    Args:
        task: The task function to decorate

    Returns:
        The decorated task function
    """

    @functools.wraps(task)
    def wrapper(*args, **kwargs):
        # Get trace ID from kwargs or generate a new one
        trace_id = kwargs.pop("trace_id", None)
        trace_id = set_trace_id(trace_id)

        # Execute task
        try:
            return task(*args, **kwargs)
        except Exception as e:
            # Log exception
            logger.exception(
                f"Task failed: {task.__name__} - {str(e)}",
                extra={
                    "trace_id": trace_id,
                    "system": "celery",
                    "task_info": {
                        "task_name": task.__name__,
                        "args": args,
                        "kwargs": kwargs,
                        "exception": str(e),
                    },
                    "event_type": "task_failure",
                },
            )
            raise

    return wrapper