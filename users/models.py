# Michael Herman gets all the credit for this: https://testdriven.io/blog/django-custom-user-model/
import uuid
import random
import secrets
import string

from django.db import connection
from django.db import models
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import CIEmailField
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.safestring import mark_safe

from .managers import CustomUserManager
from django.utils import timezone


LOCATIONS = [
    (i, i)
    for i in [
        "",
        "Afghanistan",
        "Alabama",
        "Alaska",
        "Albania",
        "Algeria",
        "Andorra",
        "Angola",
        "Anguilla",
        "Antarctica",
        "Antigua",
        "Argentina",
        "Arizona",
        "Arkansas",
        "Armenia",
        "Aruba",
        "Australia",
        "Austria",
        "Azerbaijan",
        "Bahamas",
        "Bahrain",
        "Bangladesh",
        "Barbados",
        "Barbuda",
        "Belarus",
        "Belgium",
        "Belize",
        "Benin",
        "Bermuda",
        "Bhutan",
        "Bolivia",
        "Bonaire",
        "Bosnia",
        "Botswana",
        "Bouvet Island",
        "Bouvetoya",
        "Brazil",
        "British Indian Ocean Territory",
        "British Virgin Islands",
        "Brunei Darussalam",
        "Bulgaria",
        "Burkina Faso",
        "Burundi",
        "California",
        "Cambodia",
        "Cameroon",
        "Canada",
        "Cape Verde",
        "Cayman Islands",
        "Central African Republic",
        "Chad",
        "Chile",
        "China",
        "Christmas Island",
        "Cocos (Keeling) Islands",
        "Colombia",
        "Colorado",
        "Comoros",
        "Congo",
        "Connecticut",
        "Cook Islands",
        "Costa Rica",
        "Cote d'Ivoire",
        "Croatia",
        "Cuba",
        "Curaçao",
        "Cyprus",
        "Cyprus",
        "Czech Republic",
        "Delaware",
        "Denmark",
        "Disputed Territory",
        "District of Columbia",
        "Djibouti",
        "Dominica",
        "Dominican Republic",
        "Ecuador",
        "Egypt",
        "El Salvador",
        "Equatorial Guinea",
        "Eritrea",
        "Estonia",
        "Ethiopia",
        "Falkland Islands (Malvinas)",
        "Faroe Islands",
        "Fiji",
        "Finland",
        "Florida",
        "France",
        "French Guiana",
        "French Polynesia",
        "French Southern Territories",
        "Gabon",
        "Gambia",
        "Georgia",
        "Georgia",
        "Georgia",
        "Germany",
        "Ghana",
        "Gibraltar",
        "Greece",
        "Greenland",
        "Grenada",
        "Guadeloupe",
        "Guam",
        "Guatemala",
        "Guernsey",
        "Guinea",
        "Guinea-Bissau",
        "Guyana",
        "Haiti",
        "Hawaii",
        "Heard Island and McDonald Islands",
        "Herzegovina",
        "Holy See (Vatican City State)",
        "Honduras",
        "Hong Kong",
        "Hungary",
        "Iceland",
        "Idaho",
        "Illinois",
        "India",
        "Indiana",
        "Indonesia",
        "Iowa",
        "Iran",
        "Iraq",
        "Iraq-Saudi Arabia Neutral Zone",
        "Ireland",
        "Isle of Man",
        "Israel",
        "Italy",
        "Jamaica",
        "Japan",
        "Jersey",
        "Jordan",
        "Kansas",
        "Kazakhstan",
        "Kazakhstan",
        "Kentucky",
        "Kenya",
        "Kiribati",
        "Korea",
        "Korea",
        "Kuwait",
        "Kyrgyz Republic",
        "Lao People's Democratic Republic",
        "Latvia",
        "Lebanon",
        "Lesotho",
        "Liberia",
        "Libyan Arab Jamahiriya",
        "Liechtenstein",
        "Lithuania",
        "Louisiana",
        "Luxembourg",
        "Macao",
        "Macedonia",
        "Madagascar",
        "Maine",
        "Malawi",
        "Malaysia",
        "Maldives",
        "Mali",
        "Malta",
        "Marshall Islands",
        "Martinique",
        "Maryland",
        "Massachusetts",
        "Mauritania",
        "Mauritius",
        "Mayotte",
        "Mexico",
        "Michigan",
        "Micronesia",
        "Minnesota",
        "Mississippi",
        "Missouri",
        "Moldova",
        "Monaco",
        "Mongolia",
        "Montana",
        "Montenegro",
        "Montserrat",
        "Morocco",
        "Mozambique",
        "Myanmar",
        "Namibia",
        "Nauru",
        "Nebraska",
        "Nepal",
        "Netherlands",
        "Netherlands Antilles",
        "Nevada",
        "New Caledonia",
        "New Hampshire",
        "New Jersey",
        "New Mexico",
        "New York",
        "New Zealand",
        "Nicaragua",
        "Niger",
        "Nigeria",
        "Niue",
        "Norfolk Island",
        "North Carolina",
        "North Dakota",
        "Northern Mariana Islands",
        "Norway",
        "Ohio",
        "Oklahoma",
        "Oman",
        "Oregon",
        "Pakistan",
        "Palau",
        "Palestinian Territory",
        "Panama",
        "Papua New Guinea",
        "Paraguay",
        "Pennsylvania",
        "Peru",
        "Philippines",
        "Pitcairn Islands",
        "Poland",
        "Portugal",
        "Puerto Rico",
        "Qatar",
        "Reunion",
        "Rhode Island",
        "Romania",
        "Russian Federation",
        "Russian Federation",
        "Rwanda",
        "Saint Barthelemy",
        "Saint Helena",
        "Saint Kitts and Nevis",
        "Saint Lucia",
        "Saint Martin",
        "Saint Pierre and Miquelon",
        "Saint Vincent and the Grenadines",
        "Samoa",
        "San Marino",
        "Sao Tome and Principe",
        "Saudi Arabia",
        "Senegal",
        "Serbia",
        "Seychelles",
        "Sierra Leone",
        "Singapore",
        "Sint Maarten (Netherlands)",
        "Slovakia (Slovak Republic)",
        "Slovenia",
        "Solomon Islands",
        "Somalia",
        "South Africa",
        "South Carolina",
        "South Dakota",
        "South Georgia and the South Sandwich Islands",
        "South Sudan",
        "Spain",
        "Spratly Islands",
        "Sri Lanka",
        "Sudan",
        "Suriname",
        "Svalbard & Jan Mayen Islands",
        "Swaziland",
        "Sweden",
        "Switzerland",
        "Syrian Arab Republic",
        "Taiwan",
        "Tajikistan",
        "Tanzania",
        "Tennessee",
        "Texas",
        "Thailand",
        "Timor-Leste",
        "Togo",
        "Tokelau",
        "Tonga",
        "Trinidad and Tobago",
        "Tunisia",
        "Turkey",
        "Turkey",
        "Turkmenistan",
        "Turks and Caicos Islands",
        "Tuvalu",
        "Uganda",
        "Ukraine",
        "United Arab Emirates",
        "United Kingdom of Great Britain & Northern Ireland",
        "United Nations Neutral Zone",
        "United States Minor Outlying Islands",
        "United States Minor Outlying Islands",
        "United States Virgin Islands",
        "Uruguay",
        "Utah",
        "Uzbekistan",
        "Vanuatu",
        "Venezuela",
        "Vermont",
        "Vietnam",
        "Virginia",
        "Wallis and Futuna",
        "Washington",
        "West Virginia",
        "Western Sahara",
        "Wisconsin",
        "Wyoming",
        "Yemen",
        "Zambia",
        "Zimbabwe",
        "Aland Islands",
    ]
]
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


def custom_validate_email(value):
    EmailValidator()(value)
    if value.endswith(".con"):
        raise ValidationError(_(f"{value} ends with .con and probably should be .com"), params={"value": value})


class CustomUser(AbstractUser):
    username = None
    email = CustomCIEmailField(_("email address"), unique=True, validators=[custom_validate_email])
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=MAX_LOCATION_LEN, choices=LOCATIONS, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    subscribed = models.BooleanField(
        default=True, help_text="If email address is bad then unsubscribe and deactivate them."
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.email


def is_code_unique(code):
    sql = "select users_player.id FROM users_player WHERE users_player.code = %s"
    with connection.cursor() as cursor:
        cursor.execute(sql, [code])
        row = cursor.fetchone()
    return row is None


def code_player():
    while True:
        code = secrets.token_urlsafe()[:5]
        if is_code_unique(code):
            return code


def default_data_dict():
    return {}


class Player(CustomUser):
    _code = models.CharField(
        max_length=5, db_index=True, null=True, help_text="Unique identifier useful for url parameters like referrer."
    )
    reminder = models.BooleanField(
        default=True, help_text="Send game reminder email even if the player played this weeks game already."
    )
    referrer = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="referrals")
    display_name = models.CharField(max_length=100)
    following = models.ManyToManyField("self", related_name="followers", symmetrical=False)
    is_member = models.BooleanField(
        default=False, help_text="Designates whether this player has joined the online community."
    )
    data = models.JSONField(default=default_data_dict)

    @property
    def code(self):
        return self._code

    def set_code(self):
        # arg is needed for a setter but ignored because we are having the model determine
        # viable unique codes.
        if not self._code:
            flag = True
            while flag:
                code = secrets.token_urlsafe()[:5]
                if not Player.objects.filter(_code=code).exists():
                    flag = False
            self._code = code

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.set_code()
        super(Player, self).save()

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
        return self.rank_scores.values(
            game_id=models.F("leaderboard__game__game_id"),
            game_name=models.F("leaderboard__game__name"),
            series=models.F("leaderboard__game__series__slug"),
        ).order_by("-game_id")

    @property
    def players_referred(self):
        return Player.objects.filter(referrer=self, answers__isnull=False).distinct()

    @property
    def referral_count(self):
        return len(self.players_referred.all())

    @property
    def referrals_roster(self):
        r = [
            f'<a href="/admin/users/player/{r.id}/change">{r.email} {r.display_name}</a>' for r in self.players_referred
        ]
        if r:
            n = len(r)
            r.append("")
            r.append(f"Count = {n}")
            r = "<br>".join(r)
        else:
            r = "None"
        return mark_safe(r)

    @cached_property
    def following_ids(self):
        return {p for p in self.following.values_list("id", flat=True)}

    @property
    def games_played(self):
        r = '<textarea cols="80" rows="5" style="overflow:auto;">'
        r = r + "\n".join([r["game_name"] for r in self.game_ids]) + "</textarea>"
        return mark_safe(r)


class PendingEmail(models.Model):
    referrer = models.ForeignKey(Player, null=True, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(validators=[custom_validate_email])
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
        referrer = instance.referrer
        if referrer:
            instance.following.add(referrer)
            referrer.following.add(instance)


def create_key(k=7):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=k))


class Team(models.Model):
    team_code = models.CharField(unique=True, max_length=7, default=create_key, db_index=True)
    name = models.CharField(max_length=100)
    captains = models.ManyToManyField(Player, related_name="captain_teams")
    players = models.ManyToManyField(Player, related_name="teams")

    def __str__(self):
        return self.name

    @property
    def games(self):
        return self.players.values(game_id=models.F("answers__question__game__game_id")).distinct().order_by("-game_id")
