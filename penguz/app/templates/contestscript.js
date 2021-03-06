{% load i18n %}

var messages = {
    'exactLength': '{% trans "Answer must be {0} characters long"%}',
    'lengthLimit': '{% trans "Answer must be between {0} and {1} characters long" %}',
    'allowedRangeExtra': '{% trans "Allowed characters are {0}-{1} and {2}" %}',
    'allowedRange': '{% trans "Allowed characters are {0}-{1}" %}',
    'allowedExtra': '{% trans "Allowed characters are {0}" %}',
    'unique': '{% trans "All characters must be different" %}'
};
var patterns = {
    {% for pattern in patterns %}
    "id_answer_{{pattern.id}}": "{{pattern.solution_pattern}}",
    {% endfor %}
};
$(function() {
    fi.iki.ashar.Penguz.startRemainingUpdates((new Date()).getTime());
    fi.iki.ashar.Penguz.insertFieldCheckers(patterns);
});
