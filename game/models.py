import uuid
from bulk_update_or_create import BulkUpdateOrCreateQuerySet
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.postgres.fields import ArrayField
from django.utils.text import slugify
from django.utils.functional import cached_property
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver

from sortedm2m.fields import SortedManyToManyField

from users.models import Player
from chat.models import Thread
from components.models import Component

from project.utils import our_now


class Series(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(Player, related_name='owned_series', on_delete=models.CASCADE)
    hosts = models.ManyToManyField(Player, related_name='hosted_series')
    players = models.ManyToManyField(Player, related_name='series')
    public = models.BooleanField(
        default=False,
        help_text="Anyone can see the games, results, and leaderboards in this series"
    )

    class Meta:
        verbose_name_plural = "series"

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        self.slug = self.slug or slugify(self.name)
        super().save(*args, **kwargs)


@receiver(post_save, sender=Series)
def add_owner_as_host_and_player(sender, instance, created, **kwargs):
    if created:
        instance.hosts.add(instance.owner)
        instance.players.add(instance.owner)


class Game(models.Model):
    game_id = models.IntegerField()
    name = models.CharField(max_length=100)
    hosts = models.ManyToManyField(Player, related_name='hosted_games')
    series = models.ForeignKey(Series, null=True, related_name='games', on_delete=models.CASCADE)
    start = models.DateTimeField(verbose_name="When the game starts:", null=False, blank=False)
    end = models.DateTimeField(verbose_name="When the game ends:", null=False, blank=False)
    google_form_url = models.CharField(max_length=255, blank=True,
                                       help_text="Enter the form url")
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    top_components = SortedManyToManyField(
        Component,
        blank=True,
        related_name='games_top',
        help_text=f"Components that will appear at the top of the game form."
    )

    class Meta:
        unique_together = ('series', 'game_id')
        ordering = ['-game_id']

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'{self.series}-{self.game_id}'

    def save(self, *args, **kwargs):
        game_id = kwargs.get('game_id') or self.game_id
        series = kwargs.get('series') or self.series
        if game_id is None:
            max_game_id = Game.objects.filter(series=series).aggregate(models.Max('game_id'))['game_id__max'] or 0
            game_id = max_game_id + 1
        self.game_id = game_id
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        # Need this for admin view-on-site to work.
        return f"/play/{self.uuid}"

    @cached_property
    def players_dict(self):
        if self.game_questions.first() is None:
            return Player.objects.none()
        return self.game_questions.first().raw_answers.filter(removed=False).values(
            'player', 'player__display_name').annotate(
            is_host=models.Case(
                models.When(player__in=self.hosts.values_list('id', flat=True), then=True),
                default=False,
                output_field=models.BooleanField()
            )
        )

    @property
    def players(self):
        return Player.objects.filter(
            id__in=self.game_questions.first().raw_answers.filter(removed=False).values('player')
        )

    def user_played(self, player):
        q = self.questions.filter(type=Question.ga).first()
        if q:
            return q.raw_answers.filter(player=player.id).exists()
        return False

    @property
    def teams(self):
        return self.questions.exclude(
            type=Question.op).first().raw_answers.values(
            team_id=models.F('player__teams'),
            team_name=models.F('player__teams__name')).exclude(team_id=None).distinct()

    @cached_property
    def game_questions(self):
        return self.questions.filter(type=Question.ga).order_by('number')

    @property
    def visible_questions(self):
        return self.questions.exclude(type=Question.op).order_by('number')

    @property
    def valid_raw_string_counts(self):
        return Answer.objects.values(
            'question_id', 'raw_string'
        ).filter(
            removed=False,
            question__game=self,
        ).annotate(count=models.Count('raw_string')).order_by()

    @property
    def raw_player_answers(self):
        return Answer.objects.filter(
            question__game=self,
            removed=False,
        ).order_by('player', 'question__number')

    @property
    def coded_player_answers(self):
        answer_code_subquery = AnswerCode.objects.filter(
            raw_string=models.OuterRef('raw_string'),
            question__game=self,
            question=models.OuterRef('question')
        ).values('question', 'coded_answer')
        return Answer.objects.filter(
            question__game=self,
            removed=False
        ).exclude(
            question__type__in=(Question.op, Question.ov)
        ).values_list('player', 'player__display_name', 'question__text').annotate(
            coded_answer=models.Subquery(answer_code_subquery.values('coded_answer')),
            is_host=models.Case(
                models.When(player__in=self.hosts.values_list('id', flat=True), then=True),
                default=False,
                output_field=models.BooleanField()
            )
        ).order_by('player', 'question__number')

    @property
    def max_date(self):
        return self.questions.aggregate(
            models.Max('raw_answers__timestamp'))['raw_answers__timestamp__max']

    @property
    def min_date(self):
        return self.questions.aggregate(
            models.Min('raw_answers__timestamp'))['raw_answers__timestamp__min']

    @property
    def date_range_pretty(self):
        return f'{self.start:%m/%d} - {self.end:%m/%d/%Y}'

    @property
    def is_active(self):
        now = our_now()
        return self.start <= now <= self.end

    @property
    def not_started_yet(self):
        now = our_now()
        return self.start > now

    @property
    def has_leaderboard(self):
        try:
            _ = self.leaderboard
            return True
        except ObjectDoesNotExist:
            return False


@receiver(m2m_changed, sender=Game.hosts.through)
def add_host_as_player(sender, instance, **kwargs):
    instance.series.players.add(*instance.hosts.all())


class Question(models.Model):
    game = models.ForeignKey(Game, null=True, on_delete=models.SET_NULL,
                             related_name='questions', db_index=True)
    number = models.PositiveIntegerField(null=True)
    text = models.CharField(max_length=10000)
    ga = 'GA'
    op = 'OP'
    ov = 'OV'
    QUESTION_TYPES = [
        (ga, 'Game'),
        (op, 'Optional'),
        (ov, 'Optional (visible)')
    ]
    type = models.CharField(max_length=2, choices=QUESTION_TYPES)
    choices = ArrayField(models.CharField(max_length=100, null=True), null=True, blank=True)
    image = models.FileField(upload_to='questions/', null=True, blank=True)
    caption = models.CharField(max_length=255, blank=True, default="")
    hide_default_results = models.BooleanField(default=False)
    thread = models.ForeignKey(Thread, related_name='object', null=True, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('game', 'number')

    def __str__(self):
        return self.text

    def __repr__(self):
        return f'{self.game}-{self.number}'

    def save(self, *args, **kwargs):
        if not self.pk:
            thread = Thread.objects.create()
            self.thread = thread
        if self.is_optional:
            if not self.text.startswith("OPTIONAL: "):
                self.text = "OPTIONAL: " + self.text
        super().save(*args, **kwargs)

    @property
    def is_optional(self):
        return self.type in (self.op, self.ov)


class Answer(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='answers', db_index=True)
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='raw_answers', db_index=True)
    raw_string = models.CharField(max_length=1000)
    removed = models.BooleanField(default=False,
                                  help_text='This answer should be removed from the thread')

    class Meta:
        unique_together = ('player', 'question')

    def __str__(self):
        return self.raw_string

    def __repr__(self):
        return f'{self.player}-{self.question}'

    @property
    def coded_answer(self):
        return self.question.coded_answers.get(raw_string=self.raw_string)

    @property
    def game(self):
        return self.question.game


class AnswerCode(models.Model):
    objects = BulkUpdateOrCreateQuerySet.as_manager()
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='coded_answers', db_index=True)
    raw_string = models.CharField(max_length=1000)
    coded_answer = models.CharField(max_length=1000, db_index=True)

    class Meta:
        unique_together = ('question', 'raw_string')

    def __str__(self):
        return self.coded_answer

    def __repr__(self):
        return f'{self.question}-{self.raw_string}'

    @property
    def game(self):
        return self.question.game
