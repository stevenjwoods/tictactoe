from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MaxValueValidator, MinValueValidator


GAME_STATUS_CHOICES = (
    ('F', 'First Player To Move'),
    ('S', 'Second Player To Move'),
    ('W', 'First Player Wins'),
    ('L', 'Second Player Wins'),
    ('D', 'Draw'),
)

class GamesQuerySet(models.QuerySet):
    def games_for_user(self, user):

        return self.filter(
            Q(first_player=user) | Q(second_player=user)
        )

    def active(self):
        return self.filter(
            Q(status='F') | Q(status='S')
        )


class Game(models.Model):
    first_player = models.ForeignKey(User,
                                     related_name="games_first_player",
                                     on_delete=models.CASCADE)
    second_player = models.ForeignKey(User,
                                      related_name="games_second_player",
                                      on_delete=models.CASCADE)

    start_time = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=1, default='F',
                              choices=GAME_STATUS_CHOICES)

    objects = GamesQuerySet.as_manager()  # Overwriting objects attribute, which usually
                                          # holds default manager for the model, and
                                          # replacing with our custom manager.

    def board(self):
        """
        Return a 2-dimensional list of Move objects,
        so you can ask for the state of a square at position [y][x]."""
        board = [[None for x in range(3)] for y in range(3)]
        for move in self.move_set.all():
            board[move.y][move.x] = move
        return board

    def is_users_move(self, user):
        return (user == self.first_player and self.status == 'F') or \
               (user == self.second_player and self.status == 'S')

    def new_move(self):
        """Returns a new move object with player, game and count preset"""
        if self.status not in 'FS':
            raise ValueError("Cannot make move on finished game.")

        return Move(
            game=self,
            by_first_player=self.status == 'F'
        )

    def update_after_move(self, move):
        """Update the status of the game, given the last move"""
        self.status = self._get_game_status_after_move(move)

    def _get_game_status_after_move(self, move):
        x, y = move.x, move.y
        board = self.board()
        if ((board[y][0] == board[y][1] == board[y][2]) or \
            (board[0][x] == board[1][x] == board[2][x]) or \
            (board[0][0] == board[1][1] == board[2][2]) or \
            (board[0][2] == board[1][1] == board[2][0])):
            return 'W' if move.by_first_player else "L"
        if self.move_set.count() >= 3**2:
            return 'D'
        return 'S' if self.status == 'F' else 'F'


    def get_absolute_url(self):  # Default way to tell Django what canonical URL is for a model instance
        return reverse('gameplay_detail', args=[self.id])  # Essentially same as url tag in template - constructs URL

    def __str__(self):
        return f"{self.first_player} vs {self.second_player}"


class Move(models.Model):
    x = models.IntegerField(
            validators=[MinValueValidator(0),
                        MaxValueValidator(2)]
    )
    y = models.IntegerField(
            validators=[MinValueValidator(0),
                        MaxValueValidator(2)]
    )
    comment = models.CharField(max_length=300, blank=True)
    by_first_player = models.BooleanField(editable=False)  # Will not show in forms because not editable
    game = models.ForeignKey(Game, editable=False, on_delete=models.CASCADE)

    def __eq__(self, other):
        if other is None:
            return False
        return other.by_first_player == self.by_first_player

    def save(self, *args, **kwargs):
        super(Move, self).save(*args, **kwargs)  # Save the move in the db
        self.game.update_after_move(self)
        self.game.save()  # Save the game in db after updating status
