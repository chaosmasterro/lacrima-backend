from django.db import models

class Bet(models.Model):
    id = models.BigAutoField(primary_key=True)

    event_id = models.CharField(max_length=100)
    team_a   = models.CharField(max_length=120)
    team_b   = models.CharField(max_length=120)
    sport    = models.CharField(max_length=60)
    odds     = models.FloatField(null=True, blank=True)

    # Money
    stake           = models.FloatField()         # user-entered stake (LE)
    placement_fee   = models.FloatField(default=0)
    total_charged   = models.FloatField(default=0)  # stake + placement_fee

    # VIP (phase 1: per-bet; later tie to user)
    vip_xp          = models.IntegerField(default=1)
    vip_multiplier  = models.FloatField(default=1.0)

    # Future: used when settling winners
    win_fee_rate    = models.FloatField(default=0.05)  # keep for audit

    status      = models.CharField(max_length=30, default="pending")
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sport} {self.team_a} vs {self.team_b} • {self.stake} LE"

