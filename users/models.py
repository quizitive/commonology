# Michael Herman gets all the credit for this: https://testdriven.io/blog/django-custom-user-model/
import uuid
import random
import secrets
import string

from django.db import IntegrityError
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import CIEmailField
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver

from .managers import CustomUserManager
from django.utils import timezone


LOCATIONS = [(i, i) for i in ["", "Afghanistan", "Alabama", "Alaska", "Albania", "Algeria", "Andorra", "Angola", "Anguilla", "Antarctica", "Antigua", "Argentina", "Arizona", "Arkansas", "Armenia", "Aruba", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Barbuda", "Belarus", "Belgium", "Belize", "Benin", "Bermuda", "Bhutan", "Bolivia", "Bonaire", "Bosnia", "Botswana", "Bouvet Island", "Bouvetoya", "Brazil", "British Indian Ocean Territory", "British Virgin Islands", "Brunei Darussalam", "Bulgaria", "Burkina Faso", "Burundi", "California", "Cambodia", "Cameroon", "Canada", "Cape Verde", "Cayman Islands", "Central African Republic", "Chad", "Chile", "China", "Christmas Island", "Cocos (Keeling) Islands", "Colombia", "Colorado", "Comoros", "Congo", "Connecticut", "Cook Islands", "Costa Rica", "Cote d'Ivoire", "Croatia", "Cuba", "Curaçao", "Cyprus", "Cyprus", "Czech Republic", "Delaware", "Denmark", "Disputed Territory", "District of Columbia", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Falkland Islands (Malvinas)", "Faroe Islands", "Fiji", "Finland", "Florida", "France", "French Guiana", "French Polynesia", "French Southern Territories", "Gabon", "Gambia", "Georgia", "Georgia", "Georgia", "Germany", "Ghana", "Gibraltar", "Greece", "Greenland", "Grenada", "Guadeloupe", "Guam", "Guatemala", "Guernsey", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Hawaii", "Heard Island and McDonald Islands", "Herzegovina", "Holy See (Vatican City State)", "Honduras", "Hong Kong", "Hungary", "Iceland", "Idaho", "Illinois", "India", "Indiana", "Indonesia", "Iowa", "Iran", "Iraq", "Iraq-Saudi Arabia Neutral Zone", "Ireland", "Isle of Man", "Israel", "Italy", "Jamaica", "Japan", "Jersey", "Jordan", "Kansas", "Kazakhstan", "Kazakhstan", "Kentucky", "Kenya", "Kiribati", "Korea", "Korea", "Kuwait", "Kyrgyz Republic", "Lao People's Democratic Republic", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libyan Arab Jamahiriya", "Liechtenstein", "Lithuania", "Louisiana", "Luxembourg", "Macao", "Macedonia", "Madagascar", "Maine", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Martinique", "Maryland", "Massachusetts", "Mauritania", "Mauritius", "Mayotte", "Mexico", "Michigan", "Micronesia", "Minnesota", "Mississippi", "Missouri", "Moldova", "Monaco", "Mongolia", "Montana", "Montenegro", "Montserrat", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nebraska", "Nepal", "Netherlands", "Netherlands Antilles", "Nevada", "New Caledonia", "New Hampshire", "New Jersey", "New Mexico", "New York", "New Zealand", "Nicaragua", "Niger", "Nigeria", "Niue", "Norfolk Island", "North Carolina", "North Dakota", "Northern Mariana Islands", "Norway", "Ohio", "Oklahoma", "Oman", "Oregon", "Pakistan", "Palau", "Palestinian Territory", "Panama", "Papua New Guinea", "Paraguay", "Pennsylvania", "Peru", "Philippines", "Pitcairn Islands", "Poland", "Portugal", "Puerto Rico", "Qatar", "Reunion", "Rhode Island", "Romania", "Russian Federation", "Russian Federation", "Rwanda", "Saint Barthelemy", "Saint Helena", "Saint Kitts and Nevis", "Saint Lucia", "Saint Martin", "Saint Pierre and Miquelon", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Sint Maarten (Netherlands)", "Slovakia (Slovak Republic)", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Carolina", "South Dakota", "South Georgia and the South Sandwich Islands", "South Sudan", "Spain", "Spratly Islands", "Sri Lanka", "Sudan", "Suriname", "Svalbard & Jan Mayen Islands", "Swaziland", "Sweden", "Switzerland", "Syrian Arab Republic", "Taiwan", "Tajikistan", "Tanzania", "Tennessee", "Texas", "Thailand", "Timor-Leste", "Togo", "Tokelau", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkey", "Turkmenistan", "Turks and Caicos Islands", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom of Great Britain & Northern Ireland", "United Nations Neutral Zone", "United States Minor Outlying Islands", "United States Minor Outlying Islands", "United States Virgin Islands", "Uruguay", "Utah", "Uzbekistan", "Vanuatu", "Venezuela", "Vermont", "Vietnam", "Virginia", "Wallis and Futuna", "Washington", "West Virginia", "Western Sahara", "Wisconsin", "Wyoming", "Yemen", "Zambia", "Zimbabwe", "Aland Islands"]]
MAX_LOCATION_LEN = max([len(i[0]) for i in LOCATIONS]) + 1


class CustomCIEmailField(CIEmailField):
    description = "CIEmailField forcing forms to downcase"

    def __init__(self, *args, **kwargs):
        super(CustomCIEmailField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        if value:
            return str(value).lower()
        else:
            return value


class CustomUser(AbstractUser):
    username = None
    email = CustomCIEmailField(_('email address'), unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=MAX_LOCATION_LEN, choices=LOCATIONS, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    subscribed = models.BooleanField(default=True,
                                     help_text="If email address is bad then unsubscribe and deactivate them.")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.email


def code_player():
    return secrets.token_urlsafe()[:5]
    # while True:
    # code = secrets.token_urlsafe()[:5]
    # if not Player.objects.filter(code=code).exists():
    #     return code


class Player(CustomUser):
    code = models.CharField(max_length=5, unique=True, db_index=True, default=code_player,
                            help_text="Unique identifer useful for url parameters like referrer.")
    referrer = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100)
    following = models.ManyToManyField('self', related_name='followers', symmetrical=False)
    is_member = models.BooleanField(
        default=False,
        help_text="Designates whether this player has joined the online community."
    )

    def __str__(self):
        return self.email

    @property
    def name(self):
        if self.first_name:
            return f"{self.first_name} {self.last_name}"
        elif self.display_name:
            return self.display_name
        else:
            return self.email

    @property
    def game_ids(self):
        return self.answers.values(
            game_id=models.F('question__game__game_id'), series=models.F('question__game__series__slug')).exclude(
            game_id=None).distinct().order_by('-game_id')


class PendingEmail(models.Model):
    referrer = models.ForeignKey(Player, null=True, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    created = models.DateTimeField(default=timezone.now)


@receiver(post_save, sender=Player)
def add_names_and_follow(sender, instance, created, **kwargs):
    if created:
        # we really want all names set for all new users
        if not instance.display_name:
            instance.display_name = f"{instance.first_name} {instance.last_name}".strip()
        elif not instance.first_name or not instance.last_name:
            # we're going to put the first word of display_name as first_name
            # and the rest as last_name... if they don't already exist
            parsed_name = instance.display_name.split()
            try:
                possible_first_name = parsed_name.pop(0)[:30]
                instance.first_name = instance.first_name or possible_first_name
                instance.last_name = instance.last_name or " ".join(parsed_name)[:30]
            except IndexError:
                instance.first_name = ""
                instance.last_name = ""
        instance.following.add(instance)


def create_key(k=7):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=k))


class Team(models.Model):
    team_code = models.CharField(unique=True, max_length=7, default=create_key, db_index=True)
    name = models.CharField(max_length=100)
    captains = models.ManyToManyField(Player, related_name='captain_teams')
    players = models.ManyToManyField(Player, related_name='teams')

    def __str__(self):
        return self.name

    @property
    def games(self):
        return self.players.values(
            game_id=models.F('answers__question__game__game_id')).distinct().order_by('-game_id')
