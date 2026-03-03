"""Helper utilities for SSE events."""


class TopicBuilder:
    """
    Helper for building consistent topic names.

    Provides methods for common topic patterns used in CRM and collaborative applications.

    Example:
        ```python
        topics = TopicBuilder()

        # Subscribe to comment thread updates
        topic = topics.comment_thread(123)  # "comment_thread:123"

        # Subscribe to ticket updates
        topic = topics.ticket(456)  # "ticket:456"

        # Subscribe to user-specific notifications
        topic = topics.user("user_789")  # "user:user_789"
        ```
    """

    @staticmethod
    def comment_thread(thread_id: str | int) -> str:
        """
        Build topic name for comment thread updates.

        Args:
            thread_id: Thread identifier

        Returns:
            Topic name in format "comment_thread:{thread_id}"
        """
        return f"comment_thread:{thread_id}"

    @staticmethod
    def ticket(ticket_id: str | int) -> str:
        """
        Build topic name for ticket updates.

        Args:
            ticket_id: Ticket identifier

        Returns:
            Topic name in format "ticket:{ticket_id}"
        """
        return f"ticket:{ticket_id}"

    @staticmethod
    def task(task_id: str | int) -> str:
        """
        Build topic name for task updates.

        Args:
            task_id: Task identifier

        Returns:
            Topic name in format "task:{task_id}"
        """
        return f"task:{task_id}"

    @staticmethod
    def workspace(workspace_id: str | int) -> str:
        """
        Build topic name for workspace-wide updates.

        Args:
            workspace_id: Workspace identifier

        Returns:
            Topic name in format "workspace:{workspace_id}"
        """
        return f"workspace:{workspace_id}"

    @staticmethod
    def user(user_id: str | int) -> str:
        """
        Build topic name for user-specific notifications.

        Args:
            user_id: User identifier

        Returns:
            Topic name in format "user:{user_id}"
        """
        return f"user:{user_id}"

    @staticmethod
    def custom(resource_type: str, resource_id: str | int) -> str:
        """
        Build topic name for custom resource types.

        Args:
            resource_type: Type of resource (e.g., "project", "document")
            resource_id: Resource identifier

        Returns:
            Topic name in format "{resource_type}:{resource_id}"
        """
        return f"{resource_type}:{resource_id}"
