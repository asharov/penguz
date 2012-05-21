from django import forms
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from penguz.app.models import Contest, Puzzle, Participation, Answer, UserProfile
from penguz.app.forms import AnswerForm
from datetime import datetime, timedelta
import re

def has_ended(now, contest, participation):
    time = timedelta(minutes=contest.duration)
    return contest.end_time < now or (participation and participation[0].start_time + time < now)

def set_answer(participation, key, answer):
    try:
        puzzle = Puzzle.objects.get(id=key)
        score = 0
        if puzzle.solution.lower() == answer.lower():
            score = puzzle.points
            print puzzle.solution, score
            try:
                ans = Answer.objects.get(participation=participation,
                                         puzzle=puzzle)
                ans.answer = answer
                ans.score = score
            except Answer.DoesNotExist:
                ans = Answer(participation=participation,
                             puzzle=puzzle, answer=answer,
                             score=score)
            ans.save()
    except Puzzle.DoesNotExist:
        pass

def index(request):
    contest_list = Contest.objects.all()
    return render_to_response('index.html', { 'contest_list': contest_list })

def contest(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    participation = Participation.objects.filter(user=request.user.id).filter(contest=contest.id)
    now = datetime.now()
    if (now < contest.start_time or
        not request.user.is_authenticated()):
        return render_to_response('contest.html',
                                  { 'contest': contest,
                                    'minutes': contest.duration,
                                    'seconds': '00' })
    elif has_ended(datetime.now(), contest, participation):
        return render_to_response('contestover.html', { 'contest': contest })
    elif participation:
        spent_time = (now - participation[0].start_time).total_seconds()
        difference = int(contest.duration * 60 - spent_time)
        puzzles = Puzzle.objects.filter(contest__exact=contest_id)
        form = AnswerForm(puzzles=puzzles)
        return render_to_response('contestrunning.html',
                                  { 'contest': contest,
                                    'form': form,
                                    'minutes': difference / 60,
                                    'seconds': '%02d' % (difference % 60) },
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('conteststart.html',
                                  { 'contest': contest,
                                    'minutes': contest.duration,
                                    'seconds': '00' },
                                  context_instance=RequestContext(request))

def start(request, contest_id):
    if request.method == 'POST':
        contest = get_object_or_404(Contest, pk=contest_id)
        participation = Participation(user=request.user, contest=contest)
        participation.save()
        return HttpResponseRedirect("/contest/{0}".format(contest.id))
    else:
        raise Http404

def results(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    participations = Participation.objects.filter(contest=contest.id)
    puzzles = Puzzle.objects.filter(contest=contest.id)
    answers = []
    for participation in participations:
        panswers = Answer.objects.filter(participation=participation.id)
        if panswers:
            profile = UserProfile.objects.get(user=participation.user)
            answers.append({ 'profile': profile, 'answers': panswers })
    return render_to_response('results.html', { 'contest': contest,
                                                'puzzles': puzzles,
                                                'answers': answers })

def answer(request, contest_id):
    if request.method == 'POST':
        contest = get_object_or_404(Contest, pk=contest_id)
        puzzles = Puzzle.objects.filter(contest=contest.id)
        form = AnswerForm(request.POST, puzzles=puzzles)
        if form.is_valid():
            print form.cleaned_data
            participation = get_object_or_404(Participation, contest=contest.id,
                                              user=request.user)
            prefix = re.compile("^answer_(.+)$")
            for key, answer in form.cleaned_data.items():
                print key, answer
                if len(answer) > 0:
                    match = prefix.match(key)
                    if match:
                        set_answer(participation, match.group(1), answer)
        return HttpResponseRedirect("/contest/{0}".format(contest.id))
    else:
        raise Http404
