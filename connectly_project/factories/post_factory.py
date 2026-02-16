"""
TaskFactory

The factory centralizes task creation logic, ensuring tasks are created 
with consistent attributes and validations.
"""

from posts.models import Task


class TaskFactory:
    VALID_TASK_TYPES = ["regular", "priority", "recurring"]

    @staticmethod
    def create_task(task_type, title, description, assigned_to, metadata=None):
        """
        Create a task with type-specific validation.
        
        Args:
            task_type: Type of task ("regular", "priority", or "recurring")
            title: Task title
            description: Task description
            assigned_to: User instance to assign the task to
            metadata: Optional dict with type-specific data
                - priority tasks require 'priority_level'
                - recurring tasks require 'frequency'
        
        Returns:
            Task: The created task instance
        
        Raises:
            ValueError: If task_type is invalid or required metadata is missing
        """
        if metadata is None:
            metadata = {}

        if task_type not in TaskFactory.VALID_TASK_TYPES:
            raise ValueError(f"Invalid task type. Must be one of: {TaskFactory.VALID_TASK_TYPES}")

        # Validate type-specific requirements
        if task_type == "priority" and "priority_level" not in metadata:
            raise ValueError("Priority tasks require 'priority_level' in metadata")
        if task_type == "recurring" and "frequency" not in metadata:
            raise ValueError("Recurring tasks require 'frequency' in metadata")

        return Task.objects.create(
            title=title,
            description=description,
            assigned_to=assigned_to,
            task_type=task_type,
            metadata=metadata
        )

    @staticmethod
    def create_regular_task(title, description, assigned_to):
        """Create a regular task with no additional metadata requirements."""
        return TaskFactory.create_task(
            task_type="regular",
            title=title,
            description=description,
            assigned_to=assigned_to
        )

    @staticmethod
    def create_priority_task(title, description, assigned_to, priority_level):
        """Create a priority task with the specified priority level."""
        return TaskFactory.create_task(
            task_type="priority",
            title=title,
            description=description,
            assigned_to=assigned_to,
            metadata={"priority_level": priority_level}
        )

    @staticmethod
    def create_recurring_task(title, description, assigned_to, frequency):
        """Create a recurring task with the specified frequency."""
        return TaskFactory.create_task(
            task_type="recurring",
            title=title,
            description=description,
            assigned_to=assigned_to,
            metadata={"frequency": frequency}
        )
