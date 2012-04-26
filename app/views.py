from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from penguz.app.models import Contest, Puzzle, Participation, Answer, UserProfile
from datetime import datetime, timedelta

def has_ended(now, contest, participation):
    time = timedelta(minutes=contest.duration)
    return contest.end_time < now or (participation and participation[0].start_time + time < now)

def index(request):
    contest_list = Contest.objects.all()
    return render_to_response('index.html', { 'contest_list': contest_list })

def contest(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    participation = Participation.objects.filter(user=request.user.id).filter(contest=contest.id)
    if datetime.now() < contest.start_time:
        return render_to_response('contest.html', { 'contest': contest })
    elif has_ended(datetime.now(), contest, participation):
        return render_to_response('contestover.html', { 'contest': contest })
    elif participation:
        puzzles = Puzzle.objects.filter(contest__exact=contest_id)
        return render_to_response('contestrunning.html', { 'contest': contest,
                                                           'puzzles': puzzles },
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('conteststart.html', { 'contest': contest },
                                  context_instance=RequestContext(request))

def start(request, contest_id):
    if request.method == 'POST':
        contest = get_object_or_404(Contest, pk=contest_id)
        participation = Participation(user=request.user, contest=contest)
        participation.save()
        return HttpResponseRedirect("/password/{0}".format(contest.id))
    else:
        raise Http404

def password(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    return render_to_response('password.html', { 'contest': contest })

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
