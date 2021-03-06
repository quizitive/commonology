# Michael Herman gets all the credit for this: https://testdriven.io/blog/django-custom-user-model/
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from game.utils import create_key
from .managers import CustomUserManager


LOCATIONS = [(i, i) for i in ["UNSPECIFIED", "Afghanistan", "Alabama", "Alaska", "Albania", "Algeria", "Andorra", "Angola", "Anguilla", "Antarctica", "Antigua", "Argentina", "Arizona", "Arkansas", "Armenia", "Aruba", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Barbuda", "Belarus", "Belgium", "Belize", "Benin", "Bermuda", "Bhutan", "Bolivia", "Bonaire", "Bosnia", "Botswana", "Bouvet Island", "Bouvetoya", "Brazil", "British Indian Ocean Territory", "British Virgin Islands", "Brunei Darussalam", "Bulgaria", "Burkina Faso", "Burundi", "California", "Cambodia", "Cameroon", "Canada", "Cape Verde", "Cayman Islands", "Central African Republic", "Chad", "Chile", "China", "Christmas Island", "Cocos (Keeling) Islands", "Colombia", "Colorado", "Comoros", "Congo", "Connecticut", "Cook Islands", "Costa Rica", "Cote d'Ivoire", "Croatia", "Cuba", "Curaçao", "Cyprus", "Cyprus", "Czech Republic", "Delaware", "Denmark", "Disputed Territory", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Falkland Islands (Malvinas)", "Faroe Islands", "Fiji", "Finland", "Florida", "France", "French Guiana", "French Polynesia", "French Southern Territories", "Gabon", "Gambia", "Georgia", "Georgia", "Georgia", "Germany", "Ghana", "Gibraltar", "Greece", "Greenland", "Grenada", "Guadeloupe", "Guam", "Guatemala", "Guernsey", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Hawaii", "Heard Island and McDonald Islands", "Herzegovina", "Holy See (Vatican City State)", "Honduras", "Hong Kong", "Hungary", "Iceland", "Idaho", "Illinois", "India", "Indiana", "Indonesia", "Iowa", "Iran", "Iraq", "Iraq-Saudi Arabia Neutral Zone", "Ireland", "Isle of Man", "Israel", "Italy", "Jamaica", "Japan", "Jersey", "Jordan", "Kansas", "Kazakhstan", "Kazakhstan", "Kentucky", "Kenya", "Kiribati", "Korea", "Korea", "Kuwait", "Kyrgyz Republic", "Lao People's Democratic Republic", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libyan Arab Jamahiriya", "Liechtenstein", "Lithuania", "Louisiana", "Luxembourg", "Macao", "Macedonia", "Madagascar", "Maine", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Martinique", "Maryland", "Massachusetts", "Mauritania", "Mauritius", "Mayotte", "Mexico", "Michigan", "Micronesia", "Minnesota", "Mississippi", "Missouri", "Moldova", "Monaco", "Mongolia", "Montana", "Montenegro", "Montserrat", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nebraska", "Nepal", "Netherlands", "Netherlands Antilles", "Nevada", "New Caledonia", "New Hampshire", "New Jersey", "New Mexico", "New York", "New Zealand", "Nicaragua", "Niger", "Nigeria", "Niue", "Norfolk Island", "North Carolina", "North Dakota", "Northern Mariana Islands", "Norway", "Ohio", "Oklahoma", "Oman", "Oregon", "Pakistan", "Palau", "Palestinian Territory", "Panama", "Papua New Guinea", "Paraguay", "Pennsylvania", "Peru", "Philippines", "Pitcairn Islands", "Poland", "Portugal", "Puerto Rico", "Qatar", "Reunion", "Rhode Island", "Romania", "Russian Federation", "Russian Federation", "Rwanda", "Saint Barthelemy", "Saint Helena", "Saint Kitts and Nevis", "Saint Lucia", "Saint Martin", "Saint Pierre and Miquelon", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Sint Maarten (Netherlands)", "Slovakia (Slovak Republic)", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Carolina", "South Dakota", "South Georgia and the South Sandwich Islands", "South Sudan", "Spain", "Spratly Islands", "Sri Lanka", "Sudan", "Suriname", "Svalbard & Jan Mayen Islands", "Swaziland", "Sweden", "Switzerland", "Syrian Arab Republic", "Taiwan", "Tajikistan", "Tanzania", "Tennessee", "Texas", "Thailand", "Timor-Leste", "Togo", "Tokelau", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkey", "Turkmenistan", "Turks and Caicos Islands", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom of Great Britain & Northern Ireland", "United Nations Neutral Zone", "United States Minor Outlying Islands", "United States Minor Outlying Islands", "United States Virgin Islands", "Uruguay", "Utah", "Uzbekistan", "Vanuatu", "Venezuela", "Vermont", "Vietnam", "Virginia", "Wallis and Futuna", "Washington", "West Virginia", "Western Sahara", "Wisconsin", "Wyoming", "Yemen", "Zambia", "Zimbabwe", "Aland Islands"]]
MAX_LOCATION_LEN = max([len(i[0]) for i in LOCATIONS]) + 1


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    location = models.CharField(max_length=MAX_LOCATION_LEN, choices=LOCATIONS, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    referrer = models.EmailField(_('Referrer email address'), blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class PendingEmail(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    referrer = models.EmailField(null=True)
    created = models.DateTimeField(auto_now_add=True)


class Player(CustomUser):
    display_name = models.CharField(max_length=100)
    following = models.ManyToManyField('self', related_name='followers')

    def __str__(self):
        return self.email

    @property
    def games(self):
        return self.answers.values(
            game_id=models.F('question__game__game_id')).exclude(
            game_id=None).distinct().order_by('-game_id')


class Team(models.Model):
    id = models.CharField(primary_key=True, max_length=7, default=create_key)
    name = models.CharField(max_length=100)
    admins = models.ManyToManyField(Player, related_name='admin_teams')
    players = models.ManyToManyField(Player, related_name='teams')

    def __str__(self):
        return self.name

    @property
    def games(self):
        return self.players.values(
            game_id=models.F('answers__question__game__game_id')).distinct().order_by('-game_id')
