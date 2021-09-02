from django.db import models
from users.models import Player


class Claim(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    reward = models.CharField(max_length=150, help_text="ex. Coffee Mug")
    claim_date = models.DateField(name='Claim date')
    sent_date = models.DateField(name='Sent date', blank=True, null=True)

    def __str__(self):
        return f"{self.player} claimed reward {self.reward}"


class MailingAddress(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(name="Full Name", max_length=128)
    address1 = models.CharField(name="Address line 1", max_length=128)
    address2 = models.CharField(name="Address line 2", max_length=128, blank=True)
    city = models.CharField(name="City", max_length=128)
    State = models.CharField(name="State", max_length=2)
    zip_code = models.CharField(name="ZIP / Postal code", max_length=12)
