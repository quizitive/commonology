from bulk_update_or_create import BulkUpdateOrCreateQuerySet
from django.db import models
from django.utils.text import slugify
from users.models import Player


class Series(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    hosts = models.ManyToManyField(Player, related_name='hosted_series')
    players = models.ManyToManyField(Player, related_name='series')
    public = models.BooleanField(
        default=False,
        help_text="Anyone can see the games, results, and leaderboards in this series"
    )

    class Meta:
        verbose_name_plural = "series"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = self.slug or slugify(self.name)
        super().save(*args, **kwargs)


class Game(models.Model):
    game_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)
    hosts = models.ManyToManyField(Player, related_name='hosted_games')
    series = models.ForeignKey(Series, null=True, related_name='games', on_delete=models.CASCADE)
    sheet_name = models.CharField(
        max_length=10000,
        help_text="The name of the Google Sheet which contains response data"
    )
    publish = models.BooleanField(
        default=False,
        help_text="This game can be published to the dashboard"
    )

    class Meta:
        ordering = ['-game_id']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        game_id = kwargs.get('game_id') or self.game_id
        if not game_id:
            max_game_id = Game.objects.aggregate(models.Max('game_id'))['game_id__max'] or 0
            game_id = max_game_id + 1
        self.game_id = game_id
        super().save(*args, **kwargs)

    @property
    def players(self):
        return self.questions.exclude(
            type=Question.op).first().raw_answers.values(
            'player', 'player__display_name').annotate(
            is_host=models.Case(
                models.When(player__in=self.hosts.values_list('id', flat=True), then=True),
                default=False,
                output_field=models.BooleanField()
            )
        )

    @property
    def teams(self):
        return self.questions.exclude(
            type=Question.op).first().raw_answers.values(
            team_id=models.F('player__teams'),
            team_name=models.F('player__teams__name')).exclude(team_id=None).distinct()

    @property
    def game_questions(self):
        return self.questions.exclude(type=Question.op)

    @property
    def valid_raw_string_counts(self):
        return Answer.objects.values(
            'question_id', 'raw_string'
        ).filter(
            question__game=self
        ).annotate(count=models.Count('raw_string')).order_by()

    @property
    def coded_player_answers(self):
        answer_code_subquery = AnswerCode.objects.filter(
            raw_string=models.OuterRef('raw_string'),
            question__game=self,
            question=models.OuterRef('question')
        ).values('question', 'coded_answer')
        return Answer.objects.filter(
            question__game=self).exclude(
            question__type=Question.op
        ).values_list('player', 'player__display_name', 'question__text').annotate(
            coded_answer=models.Subquery(answer_code_subquery.values('coded_answer')),
            is_host=models.Case(
                models.When(player__in=self.hosts.values_list('id', flat=True), then=True),
                default=False,
                output_field=models.BooleanField()
            )
        ).order_by('player', 'question')

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
        return f'{self.min_date:%m/%d} - {self.max_date:%m/%d/%Y}'


class Question(models.Model):
    game = models.ForeignKey(Game, null=True, on_delete=models.SET_NULL,
                             related_name='questions', db_index=True)
    text = models.CharField(max_length=10000)
    mc = 'MC'
    fr = 'FR'
    op = 'OP'
    QUESTION_TYPES = [
        (mc, 'Multiple Choice'),
        (fr, 'Free Response'),
        (op, 'Optional')
    ]
    type = models.CharField(max_length=2, choices=QUESTION_TYPES)

    def __str__(self):
        return self.text


class Answer(models.Model):
    timestamp = models.DateTimeField()
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='answers', db_index=True)
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='raw_answers', db_index=True)
    raw_string = models.CharField(max_length=1000)

    def __str__(self):
        return self.raw_string

    class Meta:
        unique_together = ('player', 'question')

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

    @property
    def game(self):
        return self.question.game
