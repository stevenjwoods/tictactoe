from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView

from .forms import MoveForm
from .models import Game


@login_required()
def game_detail(request, pk):
    game = get_object_or_404(Game, pk=pk)
    context = {'game': game}
    if game.is_users_move(request.user):
        context['form'] = MoveForm()
    return render(request,
                  "gameplay/game_detail.html",
                  context
                  )


@login_required()
def make_move(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if not game.is_users_move(request.user):
        raise PermissionDenied
    move = game.new_move()
    form = MoveForm(instance=move, data=request.POST)
    if form.is_valid():
        move.save()
        return redirect("gameplay_detail", pk)
    else:
        return render(request,
                      "gameplay/game_detail.html",
                      {'game': game, 'form': form}
                      )


class AllGamesList(ListView):  # Demo of a generic view (ListView)
    model = Game