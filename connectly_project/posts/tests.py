from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User, Task
from singletons.config_manager import ConfigManager
from singletons.logger_singleton import LoggerSingleton
from connectly_project.factories.post_factory import TaskFactory


class ConfigManagerSingletonTest(TestCase):
    """Test that ConfigManager follows Singleton pattern."""

    def test_singleton_instance(self):
        """Verify that both instances are identical."""
        config1 = ConfigManager()
        config2 = ConfigManager()
        
        self.assertIs(config1, config2)

    def test_shared_state(self):
        """Verify that changes to one instance are reflected in all instances."""
        config1 = ConfigManager()
        config2 = ConfigManager()
        
        # Change setting through first instance
        config1.set_setting("DEFAULT_TASK_PRIORITY", "High")
        
        # Verify change is visible through second instance
        self.assertEqual(config2.get_setting("DEFAULT_TASK_PRIORITY"), "High")
        
        # Reset to default for other tests
        config1.set_setting("DEFAULT_TASK_PRIORITY", "Medium")

    def test_default_settings(self):
        """Verify default settings are initialized correctly."""
        config = ConfigManager()
        
        self.assertEqual(config.get_setting("DEFAULT_TASK_PRIORITY"), "Medium")
        self.assertEqual(config.get_setting("ENABLE_NOTIFICATIONS"), True)
        self.assertEqual(config.get_setting("RATE_LIMIT"), 50)

    def test_get_all_settings(self):
        """Verify get_all_settings returns a copy of settings."""
        config = ConfigManager()
        all_settings = config.get_all_settings()
        
        self.assertIn("DEFAULT_TASK_PRIORITY", all_settings)
        self.assertIn("ENABLE_NOTIFICATIONS", all_settings)
        self.assertIn("RATE_LIMIT", all_settings)


class LoggerSingletonTest(TestCase):
    """Test that LoggerSingleton follows Singleton pattern."""

    def test_singleton_instance(self):
        """Verify that both instances are identical."""
        logger1 = LoggerSingleton()
        logger2 = LoggerSingleton()
        
        self.assertIs(logger1, logger2)

    def test_logger_is_same(self):
        """Verify that get_logger returns the same logger instance."""
        logger_singleton1 = LoggerSingleton()
        logger_singleton2 = LoggerSingleton()
        
        logger1 = logger_singleton1.get_logger()
        logger2 = logger_singleton2.get_logger()
        
        self.assertIs(logger1, logger2)

    def test_logger_name(self):
        """Verify logger has correct name."""
        logger = LoggerSingleton().get_logger()
        
        self.assertEqual(logger.name, "task_logger")


class TaskFactoryTest(TestCase):
    """Test TaskFactory for creating tasks."""

    def setUp(self):
        """Create a test user for task assignment."""
        self.user = User.objects.create(
            username="testuser",
            email="test@example.com"
        )

    def tearDown(self):
        """Clean up test data."""
        Task.objects.all().delete()
        User.objects.all().delete()

    def test_create_regular_task(self):
        """Test creating a regular task."""
        task = TaskFactory.create_task(
            task_type="regular",
            title="Test Regular Task",
            description="A regular task",
            assigned_to=self.user
        )
        
        self.assertEqual(task.task_type, "regular")
        self.assertEqual(task.title, "Test Regular Task")
        self.assertEqual(task.assigned_to, self.user)

    def test_create_priority_task(self):
        """Test creating a priority task with required metadata."""
        task = TaskFactory.create_task(
            task_type="priority",
            title="Test Priority Task",
            description="A priority task",
            assigned_to=self.user,
            metadata={"priority_level": "High"}
        )
        
        self.assertEqual(task.task_type, "priority")
        self.assertEqual(task.metadata["priority_level"], "High")

    def test_create_priority_task_without_metadata_fails(self):
        """Test that creating a priority task without priority_level raises error."""
        with self.assertRaises(ValueError) as context:
            TaskFactory.create_task(
                task_type="priority",
                title="Test Priority Task",
                description="A priority task",
                assigned_to=self.user
            )
        
        self.assertIn("priority_level", str(context.exception))

    def test_create_recurring_task(self):
        """Test creating a recurring task with required metadata."""
        task = TaskFactory.create_task(
            task_type="recurring",
            title="Test Recurring Task",
            description="A recurring task",
            assigned_to=self.user,
            metadata={"frequency": "daily"}
        )
        
        self.assertEqual(task.task_type, "recurring")
        self.assertEqual(task.metadata["frequency"], "daily")

    def test_create_recurring_task_without_metadata_fails(self):
        """Test that creating a recurring task without frequency raises error."""
        with self.assertRaises(ValueError) as context:
            TaskFactory.create_task(
                task_type="recurring",
                title="Test Recurring Task",
                description="A recurring task",
                assigned_to=self.user
            )
        
        self.assertIn("frequency", str(context.exception))

    def test_invalid_task_type_fails(self):
        """Test that invalid task type raises error."""
        with self.assertRaises(ValueError) as context:
            TaskFactory.create_task(
                task_type="invalid",
                title="Test Task",
                description="Invalid type",
                assigned_to=self.user
            )
        
        self.assertIn("Invalid task type", str(context.exception))

    def test_convenience_methods(self):
        """Test convenience factory methods."""
        # Regular task
        regular = TaskFactory.create_regular_task(
            title="Regular",
            description="A regular task",
            assigned_to=self.user
        )
        self.assertEqual(regular.task_type, "regular")
        
        # Priority task
        priority = TaskFactory.create_priority_task(
            title="Priority",
            description="A priority task",
            assigned_to=self.user,
            priority_level="Critical"
        )
        self.assertEqual(priority.task_type, "priority")
        self.assertEqual(priority.metadata["priority_level"], "Critical")
        
        # Recurring task
        recurring = TaskFactory.create_recurring_task(
            title="Recurring",
            description="A recurring task",
            assigned_to=self.user,
            frequency="weekly"
        )
        self.assertEqual(recurring.task_type, "recurring")
        self.assertEqual(recurring.metadata["frequency"], "weekly")


class TaskAPITest(APITestCase):
    """Test Task API endpoints."""

    def setUp(self):
        """Create a test user."""
        self.user = User.objects.create(
            username="apiuser",
            email="api@example.com"
        )

    def tearDown(self):
        """Clean up test data."""
        Task.objects.all().delete()
        User.objects.all().delete()

    def test_create_task_via_api(self):
        """Test creating a task through the API."""
        data = {
            "task_type": "regular",
            "title": "API Test Task",
            "description": "Created via API",
            "assigned_to": self.user.id
        }
        
        response = self.client.post('/api/tasks/create/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['task_type'], 'regular')
        self.assertIn('task_id', response.data)

    def test_create_priority_task_via_api(self):
        """Test creating a priority task through the API."""
        data = {
            "task_type": "priority",
            "title": "Priority API Task",
            "description": "Priority task via API",
            "assigned_to": self.user.id,
            "metadata": {"priority_level": "High"}
        }
        
        response = self.client.post('/api/tasks/create/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['task_type'], 'priority')

    def test_create_priority_task_without_metadata_fails(self):
        """Test that priority task without metadata fails via API."""
        data = {
            "task_type": "priority",
            "title": "Priority Task",
            "description": "Missing metadata",
            "assigned_to": self.user.id
        }
        
        response = self.client.post('/api/tasks/create/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_tasks(self):
        """Test listing all tasks."""
        # Create test tasks
        TaskFactory.create_regular_task(
            title="Task 1",
            description="First task",
            assigned_to=self.user
        )
        TaskFactory.create_regular_task(
            title="Task 2",
            description="Second task",
            assigned_to=self.user
        )
        
        response = self.client.get('/api/tasks/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_filter_tasks_by_type(self):
        """Test filtering tasks by type."""
        TaskFactory.create_regular_task(
            title="Regular Task",
            description="A regular task",
            assigned_to=self.user
        )
        TaskFactory.create_priority_task(
            title="Priority Task",
            description="A priority task",
            assigned_to=self.user,
            priority_level="High"
        )
        
        response = self.client.get('/api/tasks/?type=priority')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['task_type'], 'priority')

    def test_get_task_detail(self):
        """Test getting a specific task."""
        task = TaskFactory.create_regular_task(
            title="Detail Task",
            description="Task for detail view",
            assigned_to=self.user
        )
        
        response = self.client.get(f'/api/tasks/{task.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Detail Task')

    def test_update_task(self):
        """Test updating a task."""
        task = TaskFactory.create_regular_task(
            title="Original Title",
            description="Original description",
            assigned_to=self.user
        )
        
        data = {"title": "Updated Title"}
        response = self.client.put(f'/api/tasks/{task.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')

    def test_delete_task(self):
        """Test deleting a task."""
        task = TaskFactory.create_regular_task(
            title="Task to Delete",
            description="Will be deleted",
            assigned_to=self.user
        )
        
        response = self.client.delete(f'/api/tasks/{task.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_task_not_found(self):
        """Test 404 for non-existent task."""
        response = self.client.get('/api/tasks/9999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
