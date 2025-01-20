from django.db import migrations
from django.contrib.postgres.operations import CITextExtension


# Marc Schwarzschild wrote this - it was not created by make migrations
class Migration(migrations.Migration):
    dependencies = [
        ("users", "0006_auto_20210419_1520"),
    ]

    operations = [CITextExtension()]
