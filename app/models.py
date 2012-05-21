from django.db import models
from django_countries import CountryField
from django.contrib import admin
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

def generate_instrname(instance, filename):
    return generate_filename(instance, "instructions")

def generate_contestname(instance, filename):
    return generate_filename(instance, "contest")

def generate_filename(instance, suffix):
    if not instance.slug:
        slug_field = instance._meta.get_field('slug')
        slug_max_length = slug_field.max_length
        slug = slugify(instance.name)
        if (slug_max_length):
            slug = slug[:slug_max_length]
        slugs = [sl.values()[0] for sl in instance.__class__.objects.values('slug')]
        if slug in slugs:
            import re
            counterFinder = re.compile(r'-\d+$')
            counter = 1
            slug = slug[:slug_max_length-10]
            slug = "{0}-{1}".format(slug, counter)
            while slug in slugs:
                counter += 1
                slug = re.sub(counterFinder, "-{0}".format(counter), slug)
        instance.slug = slug
        instance.save()
    return "{0}-{1}.pdf".format(instance.slug, suffix)

class Contest(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120,editable=False)
    description = models.TextField()
    organizer = models.ForeignKey(User)
    instruction_booklet = models.FileField(upload_to=generate_instrname,
                                           blank=True)
    contest_booklet = models.FileField(upload_to=generate_contestname,
                                       blank=True)
    password = models.CharField(max_length=80,blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration = models.IntegerField()
    country = CountryField(blank=True)
    puzzle_count = models.PositiveIntegerField()

    class Meta:
        ordering = ["-start_time"]

    def __unicode__(self):
        return self.name

admin.site.register(Contest)

class Puzzle(models.Model):
    contest = models.ForeignKey(Contest)
    number = models.PositiveIntegerField()
    name = models.CharField(max_length=40)
    points = models.IntegerField()
    solution = models.CharField(max_length=60)
    solution_row_count = models.PositiveIntegerField()
    solution_row_names = models.CharField(max_length=120)
    solution_pattern = models.CharField(max_length=60)

    class Meta:
        ordering = ["contest", "number"]

    def __unicode__(self):
        return self.name

admin.site.register(Puzzle)

class Participation(models.Model):
    user = models.ForeignKey(User)
    contest = models.ForeignKey(Contest)
    start_time = models.DateTimeField(auto_now_add=True)
    last_submission = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "{0} at {1}".format(self.user.get_full_name(),
                                   self.contest.name)

admin.site.register(Participation)

class Answer(models.Model):
    participation = models.ForeignKey(Participation)
    puzzle = models.ForeignKey(Puzzle)
    answer = models.CharField(max_length=60)
    score = models.IntegerField()

    class Meta:
        ordering = ["puzzle"]

    def __unicode__(self):
        return "Answer of {0} to {1}".format(self.participation.user.get_full_name(),
                                             self.puzzle.name)
    
admin.site.register(Answer)

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    country = CountryField(blank=True)

    def __unicode__(self):
        return self.user.username

admin.site.register(UserProfile)
