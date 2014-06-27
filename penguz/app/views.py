from datetime import datetime, timedelta
from operator import itemgetter
import re
import logging

from django import forms
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.utils.translation import ugettext as _

from penguz.app.models import Contest, Puzzle, Participation, Answer, UserProfile
from penguz.app.forms import RegisterForm, ProfileForm, AnswerForm, ContestForm, PuzzleForm, ContestEditForm

logger = logging.getLogger(__name__)

def total_seconds(delta):
    return (delta.microseconds + (delta.seconds + delta.days * 24 * 3600) * 10**6) / 10**6

def has_ended(now, contest, participation):
    time = timedelta(minutes=contest.duration)
    return contest.end_time < now or (participation and participation[0].start_time + time < now)

def format_url(page, contest):
    return "/{0}/{1}/{2}".format(page, contest.id, contest.slug)

def fill_context_with_participation(context, now, participation, contest):
    spent_time = total_seconds(now - participation[0].start_time)
    difference = int(contest.duration * 60 - spent_time)
    puzzles = Puzzle.objects.filter(contest__exact=contest.id)
    answer_set = Answer.objects.filter(participation=participation[0].id)
    non_empty_answers = answer_set.exclude(answer='')
    answers = dict([(answer.puzzle.id, answer.answer) for answer in answer_set])
    form = AnswerForm(puzzles=puzzles, answers=answers)
    patterns = puzzles.values('id', 'solution_pattern')
    context.update({ 'form': form,
                     'participation': participation[0],
                     'answer_count': non_empty_answers.count(),
                     'minutes': difference / 60,
                     'seconds': '%02d' % (difference % 60),
                     'patterns': patterns })

def set_answer(participation, key, answer):
    try:
        puzzle = Puzzle.objects.get(id=key)
        score = 0
        if puzzle.solution.lower() == answer.lower():
            score = puzzle.points
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
    now = datetime.now()
    contests_with_puzzles = Puzzle.objects.all().values('contest').query
    contest_list = Contest.objects.filter(id__in=contests_with_puzzles)
    running_contest_list = contest_list.filter(start_time__lte=now,
                                               end_time__gt=now)
    future_contest_list = contest_list.filter(start_time__gt=now)
    past_contest_list = contest_list.filter(end_time__lte=now)
    return render_to_response('index.html',
                              { 'running_contest_list': running_contest_list,
                                'future_contest_list': future_contest_list,
                                'past_contest_list': past_contest_list },
                              context_instance=RequestContext(request))

def register(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        data = form.cleaned_data
        logger.info(u"Register user {0} {1} {2}".format(data['username'],
                                                        data['email'],
                                                        data['organizer']))
        if not User.objects.filter(username=data['username']).exists():
            form.save()
            new_user = authenticate(username=data['username'],
                                    password=data['password'])
            if new_user is not None:
                login(request, new_user)
                return HttpResponseRedirect(reverse('app.views.index'))
        else:
            form._errors['username'] = [_('Username already exists')]
    return render_to_response('registration/register.html',
                              { 'form': form },
                              context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_authenticated())
def own(request):
    participated_contests = Participation.objects.filter(user=request.user.id).values('contest').query
    own_contests = Contest.objects.filter(id__in=participated_contests)
    organized_contests = Contest.objects.filter(organizer=request.user.id)
    contests_with_puzzles = Puzzle.objects.all().values('contest').query
    incomplete_contests = organized_contests.exclude(id__in=contests_with_puzzles)
    complete_contests = organized_contests.filter(id__in=contests_with_puzzles)
    return render_to_response('own.html',
                              { 'own_contests': own_contests,
                                'organized_contests': organized_contests,
                                'incomplete_contests': incomplete_contests,
                                'complete_contests': complete_contests },
                              context_instance=RequestContext(request))

def help(request):
    return render_to_response('help.html',
                              context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_authenticated())
def profile(request):
    prof = UserProfile.objects.get(user=request.user)
    return render_to_response('profile.html',
                              { 'profile': prof,
                                'organizer': _('Yes') if request.user.has_perm('app.add_contest') else _('No') },
                              context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_authenticated())
def editprofile(request):
    form = ProfileForm(request.POST or None)
    if form.is_valid():
        data = form.cleaned_data
        if data.get('country'):
            profile = UserProfile.objects.get(user=request.user)
            profile.country = data['country']
            profile.save()
        if data.get('name'):
            request.user.first_name = data['name']
        if data.get('email'):
            request.user.email = data['email']
        if data.get('password'):
            request.user.set_password(data['password'])
        request.user.save()
        return HttpResponseRedirect(reverse('app.views.profile'))
    return render_to_response('editprofile.html',
                              { 'form': form },
                              context_instance=RequestContext(request))

def contest(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    participation = Participation.objects.filter(user=request.user.id).filter(contest=contest.id)
    now = datetime.now()
    if contest.organizer == request.user:
        if not participation:
            participation = [Participation(user=request.user, contest=contest)]
        participation[0].start_time = now
        participation[0].save()
    context = { 'contest': contest,
                'minutes': contest.duration,
                'seconds': '00',
                'now': now }
    if contest.organizer == request.user:
        fill_context_with_participation(context, now, participation, contest)
        return render_to_response('contestauthor.html',
                                  context,
                                  context_instance=RequestContext(request))
    elif now < contest.start_time:
        return render_to_response('contest.html',
                                  context,
                                  context_instance=RequestContext(request))
    elif has_ended(now, contest, participation):
        return render_to_response('contestover.html',
                                  context,
                                  context_instance=RequestContext(request))
    elif not request.user.is_authenticated():
        return render_to_response('contestguest.html',
                                  context,
                                  context_instance=RequestContext(request))
    elif participation:
        fill_context_with_participation(context, now, participation, contest)
        return render_to_response('contestrunning.html',
                                  context,
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('conteststart.html',
                                  context,
                                  context_instance=RequestContext(request))

def start(request, contest_id):
    if request.method == 'POST':
        contest = get_object_or_404(Contest, pk=contest_id)
        participations = Participation.objects.filter(user=request.user.id).filter(contest=contest.id)
        if not participations:
            logger.info("Start contest {0} {1}".format(request.user, contest))
            participation = Participation(user=request.user, contest=contest)
            participation.save()
        return HttpResponseRedirect(format_url("contest", contest))
    else:
        raise Http404

def results(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    participations = Participation.objects.filter(contest=contest.id)
    now = datetime.now()
    user_is_organizer = request.user == contest.organizer
    if (not user_is_organizer and
        not has_ended(now, contest, participations.filter(user=request.user.id))):
        return HttpResponseForbidden(_("You are not yet allowed to see the results of this contest"))
    preliminary = now <= contest.end_time
    puzzles = list(Puzzle.objects.filter(contest=contest.id))
    country_answers = []
    other_answers = []
    for participation in participations:
        participant_is_organizer = participation.user == contest.organizer
        if (not has_ended(now, contest, [participation])
            and (not user_is_organizer or not participant_is_organizer)):
            continue
        answers = list(Answer.objects.filter(participation=participation.id))
        if answers:
            scores = []
            total_score = 0
            for puzzle in puzzles:
                if answers and answers[0].puzzle.id == puzzle.id:
                    score = answers.pop(0).score
                    scores.append(score)
                    total_score += score;
                else:
                    scores.append('-')
            spent_time = int(total_seconds(participation.last_submission
                                           - participation.start_time))
            profile = UserProfile.objects.get(user=participation.user)
            answer = { 'profile': profile,
                       'spent_minutes': spent_time / 60,
                       'spent_seconds': "%02d" % (spent_time % 60),
                       'total_score': total_score,
                       'scores': scores }
            if contest.country and profile.country == contest.country:
                country_answers.append(answer)
            else:
                other_answers.append(answer)
    country_answers.sort(key=itemgetter('spent_minutes','spent_seconds'))
    country_answers.sort(key=itemgetter('total_score'), reverse=True)
    other_answers.sort(key=itemgetter('spent_minutes','spent_seconds'))
    other_answers.sort(key=itemgetter('total_score'), reverse=True)
    return render_to_response('results.html',
                              { 'contest': contest,
                                'puzzles': puzzles,
                                'country_answers': country_answers,
                                'other_answers': other_answers,
                                'show_email': contest.organizer == request.user,
                                'preliminary': preliminary },
                              context_instance=RequestContext(request))

def answer(request, contest_id):
    if request.method == 'POST':
        contest = get_object_or_404(Contest, pk=contest_id)
        puzzles = Puzzle.objects.filter(contest=contest.id)
        form = AnswerForm(request.POST, puzzles=puzzles)
        if form.is_valid():
            logger.info(u"Answer submission {0} {1}".format(request.user,
                                                            form.cleaned_data))
            participation = get_object_or_404(Participation, contest=contest.id,
                                              user=request.user)
            if not has_ended(datetime.now(), contest, [participation]):
                prefix = re.compile("^answer_(.+)$")
                for key, answer in form.cleaned_data.items():
                    if len(answer) > 0:
                        match = prefix.match(key)
                        if match:
                            set_answer(participation, match.group(1), answer)
                participation.save()
        return HttpResponseRedirect(format_url("contest", contest))
    else:
        raise Http404

@user_passes_test(lambda u: u.has_perm('app.add_contest'))
def create(request):
    form = ContestForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        logger.info(u"Contest creation {0} {1}".format(request.user,
                                                       form.cleaned_data))
        contest = form.save(commit=False)
        contest.organizer = request.user
        if 'instruction_booklet' in request.FILES:
            contest.instruction_booklet = request.FILES['instruction_booklet']
        if 'contest_booklet' in request.FILES:
            contest.contest_booklet = request.FILES['contest_booklet']
        contest.save()
        return HttpResponseRedirect(format_url("addpuzzles", contest))
    else:
        return render_to_response("create.html",
                                  { 'form': form,
                                    'now': datetime.now() },
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
            puzzle = form.save(commit=False)
            puzzle.contest = contest
            puzzle.number = i
            min_length = data['min_length'] if data['min_length'] else ''
            max_length = data['max_length'] if data['max_length'] else ''
            puzzle.solution_pattern = "{0}-{1} {2}-{3}{4}".format(min_length, max_length, data['min_char'], data['max_char'], data['extra_chars'])
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
    form = ContestEditForm(request.POST or None, request.FILES or None,
                           instance=contest)
    if request.POST and form.is_valid():
        logger.info(u"Edit contest {0} {1}".format(contest, form.cleaned_data))
        contest = form.save(commit=False)
        if 'instruction_booklet' in request.FILES:
            contest.instruction_booklet = request.FILES['instruction_booklet']
        if 'contest_booklet' in request.FILES:
            contest.contest_booklet = request.FILES['contest_booklet']
        contest.save()
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
