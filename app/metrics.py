"""SafeStream live metrics tracking.

Implements real-time metrics for monitoring system health and activity.
"""


class MetricsTracker:
    """Tracks live metrics for SafeStream application.

    Metrics tracked:
    - viewer_count: Current number of active WebSocket connections
    - gift_count: Cumulative total of gift events since server start
    - toxic_pct: Cumulative percentage of toxic chat messages since server start
    """

    def __init__(self):
        self.gift_count = 0
        self.chat_message_total = 0
        self.toxic_message_total = 0

    def get_viewer_count(self, connected: dict) -> int:
        """Get current number of active WebSocket connections.

        Args:
            connected: Dictionary of connected WebSocket clients

        Returns:
            Number of active connections
        """
        return len(connected)

    def increment_gift_count(self) -> None:
        """Increment the cumulative gift count."""
        self.gift_count += 1

    def increment_chat_message(self, is_toxic: bool) -> None:
        """Increment chat message counters.

        Args:
            is_toxic: Whether the message was flagged as toxic
        """
        self.chat_message_total += 1
        if is_toxic:
            self.toxic_message_total += 1

    def get_toxic_percentage(self) -> float:
        """Get cumulative percentage of toxic messages.

        Returns:
            Percentage of toxic messages (0.0-100.0), or 0.0 if no messages
        """
        if self.chat_message_total == 0:
            return 0.0
        return (self.toxic_message_total / self.chat_message_total) * 100.0

    def get_metrics(self, connected: dict) -> dict:
        """Get all current metrics.

        Args:
            connected: Dictionary of connected WebSocket clients

        Returns:
            Dictionary containing all metrics
        """
        return {
            "viewer_count": self.get_viewer_count(connected),
            "gift_count": self.gift_count,
            "toxic_pct": self.get_toxic_percentage(),
        }

    def reset(self) -> None:
        """Reset all metrics counters to zero."""
        self.gift_count = 0
        self.chat_message_total = 0
        self.toxic_message_total = 0


# Global metrics tracker instance
metrics = MetricsTracker()
