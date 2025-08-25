import uuid
from django.db import models

class Bet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.CharField(max_length=128)
    team_a = models.CharField(max_length=128)
    team_b = models.CharField(max_length=128)
    sport = models.CharField(max_length=64)
    odds = models.FloatField(null=True, blank=True)
    stake = models.FloatField()
    status = models.CharField(max_length=16, default="pending")  # pending|won|lost
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
