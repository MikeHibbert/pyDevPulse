"""Huey integration for DevPulse."""

import functools
import inspect
import json
import logging
import time
from typing import Any, Callable, Dict, Optional, Union

from huey import Huey

from ..core import get_trace_id, set_trace_id

# Setup logger
logger = logging.getLogger("devpulse.integrations.huey")


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


def _pre_execute_hook(task, task_id, args, kwargs):
    """Hook that runs before task execution.

    Args:
        task: The task being executed
        task_id: The task ID
        args: The task arguments
        kwargs: The task keyword arguments
    """
    # Get trace ID from kwargs or generate a new one
    trace_id = kwargs.pop("trace_id", None) if kwargs else None
    trace_id = set_trace_id(trace_id)

    # Log task start
    task_name = task.name if hasattr(task, "name") else task.__name__
    task_info = _get_task_info(task_id, task_name, args, kwargs)
    
    logger.info(
        f"Task started: {task_name}[{task_id}]",
        extra={
            "trace_id": trace_id,
            "system": "huey",
            "task_info": task_info,
            "event_type": "task_start",
        },
    )
    
    return trace_id


def _post_execute_hook(task, task_id, args, kwargs, result, trace_id):
    """Hook that runs after successful task execution.

    Args:
        task: The task being executed
        task_id: The task ID
        args: The task arguments
        kwargs: The task keyword arguments
        result: The task result
        trace_id: The trace ID
    """
    # Set trace ID in context
    set_trace_id(trace_id)
    
    # Convert result to string
    try:
        result_str = str(result)
    except Exception:
        result_str = "<not serializable>"

    # Log task completion
    task_name = task.name if hasattr(task, "name") else task.__name__
    task_info = _get_task_info(task_id, task_name, args, kwargs)
    task_info["result"] = result_str

    logger.info(
        f"Task completed: {task_name}[{task_id}]",
        extra={
            "trace_id": trace_id,
            "system": "huey",
            "task_info": task_info,
            "event_type": "task_success",
        },
    )


def _error_hook(task, task_id, args, kwargs, exception, trace_id):
    """Hook that runs when task execution fails.

    Args:
        task: The task being executed
        task_id: The task ID
        args: The task arguments
        kwargs: The task keyword arguments
        exception: The exception that occurred
        trace_id: The trace ID
    """
    # Set trace ID in context
    set_trace_id(trace_id)
    
    # Convert exception to string
    try:
        exception_str = str(exception)
    except Exception:
        exception_str = "<not serializable>"

    # Log task failure
    task_name = task.name if hasattr(task, "name") else task.__name__
    task_info = _get_task_info(task_id, task_name, args, kwargs)
    task_info["exception"] = exception_str

    logger.error(
        f"Task failed: {task_name}[{task_id}] - {exception_str}",
        extra={
            "trace_id": trace_id,
            "system": "huey",
            "task_info": task_info,
            "event_type": "task_failure",
        },
    )


def setup_huey_tracing(huey_instance: Huey) -> None:
    """Set up DevPulse tracing for Huey.

    This function adds hooks to Huey to capture task execution details.

    Args:
        huey_instance: The Huey instance
    """
    # Store original task method
    original_task = huey_instance.task
    
    # Override task method to add tracing
    def traced_task(fn=None, **kwargs):
        def decorator(func):
            # Create the task using the original method
            task = original_task(func, **kwargs)
            
            # Store the original execute method
            original_execute = task.execute
            
            # Override execute method to add tracing
            def execute_with_tracing(*args, **kwargs):
                task_id = getattr(task, "id", str(time.time()))
                
                # Pre-execution hook
                trace_id = _pre_execute_hook(task, task_id, args, kwargs)
                
                try:
                    # Execute the task
                    result = original_execute(*args, **kwargs)
                    
                    # Post-execution hook
                    _post_execute_hook(task, task_id, args, kwargs, result, trace_id)
                    
                    return result
                except Exception as e:
                    # Error hook
                    _error_hook(task, task_id, args, kwargs, e, trace_id)
                    raise
            
            # Replace the execute method
            task.execute = execute_with_tracing
            
            return task
        
        # Handle case where decorator is called with or without arguments
        if fn is not None:
            return decorator(fn)
        return decorator
    
    # Replace the task method
    huey_instance.task = traced_task
    
    # Log initialization
    logger.info("DevPulse tracing set up for Huey")


def trace_task(task_function):
    """Decorator for tracing Huey tasks.

    This decorator adds trace ID propagation to Huey tasks. It extracts
    the trace ID from the task keyword arguments and sets it in the context
    before executing the task.

    Args:
        task_function: The task function to decorate

    Returns:
        The decorated task function
    """
    @functools.wraps(task_function)
    def wrapper(*args, **kwargs):
        # Get trace ID from kwargs or generate a new one
        trace_id = kwargs.pop("trace_id", None)
        trace_id = set_trace_id(trace_id)

        # Execute task
        try:
            return task_function(*args, **kwargs)
        except Exception as e:
            # Log exception
            logger.exception(
                f"Task failed: {task_function.__name__} - {str(e)}",
                extra={
                    "trace_id": trace_id,
                    "system": "huey",
                    "task_info": {
                        "task_name": task_function.__name__,
                        "args": args,
                        "kwargs": kwargs,
                        "exception": str(e),
                    },
                    "event_type": "task_failure",
                },
            )
            raise

    return wrapper