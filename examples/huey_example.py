"""Example Huey application with DevPulse integration."""

import logging
import random
import time
from typing import Dict, Any

from huey import RedisHuey

import devpulse
from devpulse.integrations import setup_huey_tracing

# Initialize DevPulse
devpulse.init(websocket_url="ws://localhost:8000/ws")

# Create Huey instance
huey = RedisHuey(
    'tasks',
    host='localhost',
    port=6379,
    db=0,
)

# Setup DevPulse tracing for Huey
setup_huey_tracing(huey)

# Setup logger
logger = logging.getLogger("example")
logger.setLevel(logging.INFO)


@huey.task()
def add(x: int, y: int) -> int:
    """Add two numbers.

    Args:
        x: First number
        y: Second number

    Returns:
        Sum of x and y
    """
    logger.info(f"Adding {x} + {y}")
    # Simulate work
    time.sleep(1)
    return x + y


@huey.task()
def multiply(x: int, y: int) -> int:
    """Multiply two numbers.

    Args:
        x: First number
        y: Second number

    Returns:
        Product of x and y
    """
    logger.info(f"Multiplying {x} * {y}")
    # Simulate work
    time.sleep(1)
    return x * y


@huey.task()
def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process data.

    Args:
        data: Data to process

    Returns:
        Processed data
    """
    logger.info(f"Processing data: {data}")
    # Simulate work
    time.sleep(2)
    
    # Randomly fail sometimes to demonstrate error handling
    if random.random() < 0.2:
        raise ValueError("Random failure in data processing")
    
    # Process data
    result = {}
    for key, value in data.items():
        if isinstance(value, (int, float)):
            result[key] = value * 2
        elif isinstance(value, str):
            result[key] = value.upper()
        else:
            result[key] = value
    
    return result


@huey.task()
def failing_task() -> None:
    """A task that always fails.

    This task is used to demonstrate error handling.
    """
    logger.info("Running a task that will fail")
    # Simulate work
    time.sleep(1)
    # Raise an exception
    raise ValueError("This task always fails")


def main():
    """Run example tasks."""
    # Enqueue some tasks
    add_result = add(2, 3)
    multiply_result = multiply(4, 5)
    process_result = process_data({"name": "test", "value": 42})
    failing_result = failing_task()
    
    # Print results
    print(f"Add result: {add_result.get(blocking=True)}")
    print(f"Multiply result: {multiply_result.get(blocking=True)}")
    
    try:
        print(f"Process result: {process_result.get(blocking=True)}")
    except Exception as e:
        print(f"Process task failed: {e}")
    
    try:
        failing_result.get(blocking=True)
    except Exception as e:
        print(f"Failing task failed as expected: {e}")


if __name__ == "__main__":
    main()