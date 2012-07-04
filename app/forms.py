from django import forms
from django_countries import countries
from django.utils.translation import ugettext_lazy
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User

from penguz.app import models

class RegisterForm(forms.Form):
    username = forms.CharField(label=ugettext_lazy('Username'), max_length=30)
    email = forms.EmailField(label=ugettext_lazy('Email address'),
                             max_length=80)
    name = forms.CharField(label=ugettext_lazy('Full name'), max_length=80,
                           required=False)
    country = forms.ChoiceField(label=ugettext_lazy('Nationality'),
                                choices=[('', '----')] + list(countries.COUNTRIES),
                                required=False)
    password = forms.CharField(label=ugettext_lazy('Password'), max_length=60,
                               widget=forms.PasswordInput)
    repeat_password = forms.CharField(label=ugettext_lazy('Confirm password'),
                                      max_length=60, widget=forms.PasswordInput)
    organizer = forms.BooleanField(label=ugettext_lazy('Request to be contest organizer'),
                                   required=False)

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        password = cleaned_data.get('password')
        repeat_password = cleaned_data.get('repeat_password')
        if password and repeat_password and password != repeat_password:
            raise forms.ValidationError(_('Passwords do not match'))
        return cleaned_data

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(data['username'], data['email'],
                                        data['password'])
        user.first_name = data.get('name')
        if not user.first_name:
            user.first_name = user.username
        profile = models.UserProfile(user=user, country=data.get('country'))
        user.save()
        profile.save()

class AnswerWidget(forms.MultiWidget):

    def __init__(self, size=1, names=['Answer'], attrs=None):
        widgets = []
        self.size = size
        self.names = names
        while size > 0:
            widgets.append(forms.TextInput(attrs={'size': 20}))
            size -= 1
        super(AnswerWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return value.split(',')
        else:
            return [''] * self.size

    def format_output(self, rendered_widgets):
        result = u''
        i = 0
        for widget in rendered_widgets:
            if i > 0:
                result += u'</tr><tr>'
            result += u'<td>' + self.names[i] +  u'</td>'
            result += u'<td>' + widget + u'</td>'
            i += 1
        return result

class AnswerSize(object):
    def get_size(self):
        return self._size
    def set_size(self, value):
        self._size = value
    size = property(get_size, set_size)

class AnswerField(forms.MultiValueField, AnswerSize):

    def __init__(self, size=1, names=['Answer'], *args, **kwargs):
        self.widget = AnswerWidget(size, names)
        fields = []
        i = 0
        while i < size:
            fields.append(forms.CharField(label=names[i], max_length=20))
            i += 1
        super(AnswerField, self).__init__(fields, *args, **kwargs)

    def compress(self, data):
        if data:
            return ','.join(data)
        else:
            return ''

class AnswerForm(forms.Form):

    def __init__(self, *args, **kwargs):
        puzzles = kwargs.pop('puzzles')
        answers = kwargs.pop('answers') if 'answers' in kwargs else {}
        super(AnswerForm, self).__init__(*args, **kwargs)
        for puzzle in puzzles:
            names = puzzle.solution_row_names.split(',')
            field = AnswerField(puzzle.solution_row_count, names,
                                label=puzzle.name, required=False)
            field.size = puzzle.solution_row_count
            if puzzle.id in answers:
                field.initial = answers[puzzle.id]
            self.fields['answer_{0}'.format(puzzle.id)] = field

class ContestForm(forms.ModelForm):
    class Meta:
        model = models.Contest
        exclude = ('slug', 'organizer',)

class PuzzleForm(forms.ModelForm):
    min_length = forms.IntegerField(label=ugettext_lazy('Solution minimum length'),
                                    required=False)
    max_length = forms.IntegerField(label=ugettext_lazy('Solution maximum length'),
                                    required=False)
    min_char = forms.CharField(label=ugettext_lazy('First allowed character'),
                               max_length=1, required=False)
    max_char = forms.CharField(label=ugettext_lazy('Last allowed character'),
                               max_length=1, required=False)
    extra_chars = forms.CharField(label=ugettext_lazy('Additional allowed characters'),
                                  required=False)
    pattern_unique = forms.BooleanField(label=ugettext_lazy('No repetition'),
                                        required=False)

    class Meta:
        model = models.Puzzle
        exclude = ('contest', 'number', 'solution_pattern')

    def clean(self):
        cleaned_data = super(PuzzleForm, self).clean()
        min_length = cleaned_data.get('min_length')
        max_length = cleaned_data.get('max_length')
        if min_length and max_length and min_length > max_length:
            raise forms.ValidationError(_('Minimum length must not be larger than maximum length'))
        min_char = cleaned_data.get('min_char')
        max_char = cleaned_data.get('max_char')
        if min_char and max_char and min_char[0] > max_char[0]:
            raise forms.ValidationError(_('First allowed character must come before the last allowed character'))
        return cleaned_data

class ContestEditForm(forms.ModelForm):
    class Meta:
        model = models.Contest
        fields = ('description', 'instruction_booklet', 'contest_booklet',
                  'password', 'start_time', 'end_time',)
