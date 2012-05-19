from django import forms

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
            result += self.names[i] + widget
            i += 1
        return result

class AnswerField(forms.MultiValueField):

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
        super(AnswerForm, self).__init__(*args, **kwargs)
        for puzzle in puzzles:
            names = puzzle.solution_row_names.split(',')
            self.fields['answer_{0}'.format(puzzle.id)] = \
                AnswerField(puzzle.solution_row_count, names, label=puzzle.name,
                            required=False)
