"""Example Celery application with DevPulse integration."""

import logging
import random
import time
from typing import Dict, Any

from celery import Celery

import devpulse
from devpulse.integrations import setup_celery_tracing

# Initialize DevPulse
devpulse.init(websocket_url="ws://localhost:8000/ws")

# Create Celery app
app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

# Setup DevPulse tracing for Celery
setup_celery_tracing(app)

# Setup logger
logger = logging.getLogger("example")
logger.setLevel(logging.INFO)


@app.task(bind=True)
def add(self, x, y):
    """Add two numbers."""
    trace_id = devpulse.get_trace_id()
    logger.info(f"Adding {x} + {y} with trace ID: {trace_id}")

    # Simulate random errors for demonstration
    if random.random() < 0.2:
        logger.error(f"Error adding {x} + {y}")
        raise ValueError(f"Random error while adding {x} + {y}")

    # Simulate slow task for demonstration
    if random.random() < 0.3:
        time.sleep(2)
        logger.warning(f"Slow task for adding {x} + {y}")

    result = x + y
    logger.info(f"Result of {x} + {y} = {result}")
    return result


@app.task(bind=True)
def multiply(self, x, y):
    """Multiply two numbers."""
    trace_id = devpulse.get_trace_id()
    logger.info(f"Multiplying {x} * {y} with trace ID: {trace_id}")

    # Simulate random errors for demonstration
    if random.random() < 0.2:
        logger.error(f"Error multiplying {x} * {y}")
        raise ValueError(f"Random error while multiplying {x} * {y}")

    result = x * y
    logger.info(f"Result of {x} * {y} = {result}")
    return result


@app.task(bind=True)
def divide(self, x, y):
    """Divide two numbers."""
    trace_id = devpulse.get_trace_id()
    logger.info(f"Dividing {x} / {y} with trace ID: {trace_id}")

    # Check for division by zero
    if y == 0:
        logger.error(f"Division by zero error: {x} / {y}")
        raise ZeroDivisionError(f"Cannot divide {x} by zero")

    result = x / y
    logger.info(f"Result of {x} / {y} = {result}")
    return result


@app.task(bind=True)
def complex_calculation(self, x, y, z):
    """Perform a complex calculation using multiple tasks."""
    trace_id = devpulse.get_trace_id()
    logger.info(f"Starting complex calculation with trace ID: {trace_id}")

    # Chain tasks together
    add_result = add.delay(x, y)
    add_value = add_result.get()

    multiply_result = multiply.delay(add_value, z)
    multiply_value = multiply_result.get()

    # Final result
    logger.info(f"Complex calculation result: {multiply_value}")
    return multiply_value


if __name__ == "__main__":
    # Example usage
    print("Starting Celery example...")
    print("Make sure Redis is running on localhost:6379")
    print("\nTo run Celery worker:")
    print("celery -A celery_example worker --loglevel=info")
    print("\nTo run tasks:")
    print("python -c 'from celery_example import add; add.delay(2, 3)'")
    print("python -c 'from celery_example import complex_calculation; complex_calculation.delay(2, 3, 4)'")