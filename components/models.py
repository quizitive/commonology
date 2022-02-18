from ckeditor_uploader.fields import RichTextUploadingField

from django.db import models
from django.template.loader import render_to_string

from project.utils import our_now, quick_cache


class Location(models.Model):
    app_name = models.CharField(max_length=64, help_text='The django app name of the location.')
    location = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text='The exact location. Leave blank for all app locations.'
    )

    class Meta:
        unique_together = ('app_name', 'location')

    def __str__(self):
        if not (loc := self.location):
            loc = 'ALL'
        return f"{self.app_name}:{loc}"


class Component(models.Model):
    name = models.CharField(max_length=150, unique=True)
    message = RichTextUploadingField(null=True, blank=True)
    template = models.CharField(max_length=150, default='components/simple_component.html')
    context = models.JSONField(default=dict, blank=True)
    locations = models.ManyToManyField(
        Location,
        blank=True,
        related_name='components',
        help_text=f'Make this component available to these apps/locations. NOTE: This does not automatically '
                  f'make the component appear in these locations, that must be configured explicitly.'
    )

    def __str__(self):
        return f"{self.name}"

    @property
    def render(self):
        self.context['component'] = self
        return render_to_string(self.template, self.context)

    @property
    def css_name(self):
        return self.name.lower().replace(' ', '-')


class SponsorComponent(Component):
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def __repr__(self):
        return

    @property
    def is_active(self):
        if not self.start_date or not self.end_date:
            return False
        return self.start_date <= our_now() < self.end_date

    @classmethod
    def render_active_sponsor_components(cls):
        now = our_now()
        active_components = SponsorComponent.objects.filter(start_date__lte=now, end_date__gt=now)
        return [component.render for component in active_components]
