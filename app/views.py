from datetime import datetime, timedelta
import re

from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import user_passes_test
from django.utils.translation import ugettext as _

from penguz.app.models import Contest, Puzzle, Participation, Answer, UserProfile
from penguz.app.forms import AnswerForm, ContestForm, PuzzleForm, ContestEditForm

def has_ended(now, contest, participation):
    time = timedelta(minutes=contest.duration)
    return contest.end_time < now or (participation and participation[0].start_time + time < now)

def format_url(page, contest):
    return "/{0}/{1}/{2}".format(page, contest.id, contest.slug)

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
    contests_with_puzzles = Puzzle.objects.all().values('contest').query
    contest_list = Contest.objects.filter(id__in=contests_with_puzzles)
    return render_to_response('index.html',
                              { 'contest_list': contest_list,
                                'creatable': request.user.has_perm('app.add_contest') })

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
    elif contest.organizer == request.user:
        return render_to_response('contestauthor.html',
                                  { 'contest': contest,
                                    'minutes': contest.duration,
                                    'seconds': '00' })
    elif has_ended(now, contest, participation):
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
        return HttpResponseRedirect(format_url("contest", contest))
    else:
        raise Http404

def results(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    participations = Participation.objects.filter(contest=contest.id)
    puzzles = list(Puzzle.objects.filter(contest=contest.id))
    all_answers = []
    for participation in participations:
        answers = list(Answer.objects.filter(participation=participation.id))
        if answers:
            scores = []
            for puzzle in puzzles:
                if answers and answers[0].puzzle.id == puzzle.id:
                    scores.append(answers.pop(0).score)
                else:
                    scores.append('-')
            profile = UserProfile.objects.get(user=participation.user)
            all_answers.append({ 'profile': profile, 'scores': scores })
    return render_to_response('results.html', { 'contest': contest,
                                                'puzzles': puzzles,
                                                'answers': all_answers })

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
        return HttpResponseRedirect(format_url("contest", contest))
    else:
        raise Http404

@user_passes_test(lambda u: u.has_perm('app.add_contest'))
def create(request):
    form = ContestForm(request.POST or None)
    if form.is_valid():
        contest = form.save(commit=False)
        contest.organizer = request.user
        contest.save()
        return HttpResponseRedirect(format_url("addpuzzles", contest))
    else:
        return render_to_response("create.html",
                                  { 'form': form },
                                  context_instance=RequestContext(request))

def addpuzzles(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    if contest.organizer != request.user:
        return HttpResponseForbidden(_("You are not allowed to edit this contest"))
    PuzzleFormset = formset_factory(PuzzleForm, extra=contest.puzzle_count)
    formset = PuzzleFormset(request.POST or None)
    if formset.is_valid():
        i = 1
        for form in formset:
            data = form.cleaned_data
            print data
            puzzle = form.save(commit=False)
            puzzle.contest = contest
            puzzle.number = i
            puzzle.solution_pattern = "{0}-{1} {2}-{3}{4}".format(data['min_length'], data['max_length'], data['min_char'], data['max_char'], data['extra_chars'])
            if data['pattern_unique']:
                puzzle.solution_pattern += ' !'
            puzzle.save()
            i += 1
        return HttpResponseRedirect("/")
    else:
        return render_to_response("addpuzzles.html",
                                  { 'formset': formset,
                                    'contest': contest },
                                  context_instance=RequestContext(request))

def edit(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    if contest.organizer != request.user:
        return HttpResponseForbidden(_("You are not allowed to edit this contest"))
    form = ContestEditForm(request.POST or None, instance=contest)
    if request.POST and form.is_valid():
        form.save()
        return HttpResponseRedirect("/")
    return render_to_response('edit.html',
                              { 'form': form,
                                'contest': contest },
                              context_instance=RequestContext(request))

def editpuzzles(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    if contest.organizer != request.user:
        return HttpResponseForbidden(_("You are not allowed to edit this contest"))
    puzzles = Puzzle.objects.filter(contest=contest.id)
    PuzzleEditFormset = modelformset_factory(Puzzle, extra=0,
                                             fields = ('points', 'solution',))
    formset = PuzzleEditFormset(request.POST or None, queryset=puzzles)
    if request.POST and formset.is_valid():
        formset.save()
        return HttpResponseRedirect("/")
    return render_to_response("editpuzzles.html",
                              { 'formset': formset,
                                'contest': contest },
                              context_instance=RequestContext(request))
