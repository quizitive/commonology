from django.db import models
from users.models import Player


class Claim(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    reward = models.CharField(max_length=150, default="First edition coffee mug", help_text="ex. Coffee mug")
    claim_date = models.DateField(verbose_name="Claim date", auto_now_add=True)
    sent_date = models.DateField(verbose_name="Sent date", blank=True, null=True)

    class Meta:
        unique_together = ["player", "reward"]

    def __str__(self):
        return f"{self.player} claimed reward {self.reward}"


class MailingAddress(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(verbose_name="Full Name", max_length=128)
    address1 = models.CharField(verbose_name="Address line 1", max_length=128)
    address2 = models.CharField(verbose_name="Address line 2", max_length=128, blank=True)
    city = models.CharField(verbose_name="City", max_length=128)
    state = models.CharField(verbose_name="State", max_length=2)
    zip_code = models.CharField(verbose_name="ZIP / Postal code", max_length=12)

    def __str__(self):
        return (
            f"{self.name}<br>"
            f"{self.address1}<br>"
            f"{self.address2}<br>"
            f"{self.city}, {self.state}, {self.zip_code}"
        )
