String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
	return typeof args[number] !== 'undefined'
	    ? args[number]
	    : match;
    });
};
Object.prototype.isEmpty = function() {
    for (var prop in this) {
	if (this.hasOwnProperty(prop)) {
	    return false;
	}
    }
    return true;
};
var fi;
if (!fi) {
    fi = {};
} else if (typeof fi != 'object') {
    throw new Error("fi exists and is not an object");
}
if (!fi.iki) {
    fi.iki = {};
} else if (typeof fi.iki != 'object') {
    throw new Error("fi.iki exists and is not an object");
}
if (!fi.iki.ashar) {
    fi.iki.ashar = {};
} else if (typeof fi.iki.ashar != 'object') {
    throw new Error("fi.iki.ashar exists and is not an object");
}
fi.iki.ashar.Penguz = function() {
    var remainingIntervalId = null;
    var invalidInputs = {};
    function padNumberWithZero (number) {
	return (number < 10 ? "0" : "") + number;
    }
    function parsePattern (pattern) {
	var parsed = {};
	var array = pattern.split(" ");
	var lens = array[0].split("-");
	parsed.minLength = lens[0] || 0;
	parsed.maxLength = lens[1] || 999; // Large, longer than field length
	var allowed = '';
	if (array[1].charAt(0) !== '-' && array[1].charAt(1) === '-') {
	    parsed.minChar = array[1].charAt(0);
	    parsed.maxChar = array[1].charAt(2);
	    allowed = array[1].substring(0, 3);
	    array[1] = array[1].slice(3);
	} else if (array[1].charAt(0) === '-') {
	    array[1] = array[1].slice(1);
	}
        var i = array[1].indexOf('-');
        if (i >= 0 && i < array[1].length - 1) {
	    array[1] = array[1].substring(0, i) + array[1].substring(i + 1);
            array[1] += '-';
        }
	allowed += array[1];
	parsed.extraChars = array[1].split('').join(', ');
	if (allowed) {
	    allowed = allowed.replace(/\\/, "\\\\");
	    parsed.pattern = new RegExp('^[' + allowed + ']*$', 'i');
	} else {
	    parsed.pattern = new RegExp('.*');
	}
	parsed.unique = array[2] && array[2] === "!";
	return parsed;
    }
    function checkUnique(value) {
	for (var i = 0; i < value.length - 1; ++i) {
	    if (value.indexOf(value.charAt(i), i + 1) >= 0) {
		return false;
	    }
	}
	return true;
    }
    function checkField(pattern, value) {
	if (value.length > 0) {
	    if (value.length < pattern.minLength
		|| value.length > pattern.maxLength) {
		if (pattern.minLength === pattern.maxLength) {
		    return messages.exactLength.format(pattern.minLength);
		} else {
		    return messages.lengthLimit.format(pattern.minLength,
						       pattern.maxLength);
		}
	    } else if (!pattern.pattern.test(value)) {
		if (pattern.minChar) {
		    if (pattern.extraChars) {
			return messages.allowedRangeExtra.
			    format(pattern.minChar, pattern.maxChar,
				   pattern.extraChars);
		    } else {
			return messages.allowedRange.format(pattern.minChar,
							    pattern.maxChar);
		    }
		} else {
		    return messages.allowedExtra.format(pattern.extraChars);
		}
	    } else if (pattern.unique && !checkUnique(value)) {
		return messages.unique;
	    } else {
		return '';
	    }
	} else {
	    return '';
	}
    }
    return {
	startRemainingUpdates: function(loadTime) {
	    var self = this;
	    var initialRemaining = ($("#min-remaining").text() | 0) * 60 +
		($("#sec-remaining").text() | 0);
	    function update() {
		var currentTime = (new Date()).getTime();
		var diff = (currentTime - loadTime) / 1000 | 0;
		var remaining = initialRemaining - diff;
		if (remaining < 0) {
		    remaining = 0;
		    self.stopRemainingUpdates();
		}
		$("#min-remaining").text((remaining / 60) | 0);
		$("#sec-remaining").text(padNumberWithZero(remaining % 60));
	    }
	    remainingIntervalId = window.setInterval(update, 200);
	},
	stopRemainingUpdates: function() {
	    if (remainingIntervalId) {
		window.clearInterval(remainingIntervalId);
		remainingIntervalId = null;
	    }
	},
	insertFieldCheckers: function(patterns) {
	    for (var p in patterns) {
		if (typeof patterns[p] === 'string') {
		    patterns[p] = parsePattern(patterns[p]);
		}
	    }
	    var submitButton = $('button[name=answer]');
	    var re = new RegExp('^(id_answer_\\d+)_.*$');
	    $('table[id=answer_submission_form]').
		find('input[id^=id_answer_]').
		each(function (i) {
		    var match = re.exec($(this).attr('id'));
		    if (match) {
			$(this).after('<span class="invalid-input-note"></span>');
			$(this).keyup(function() {
			    var check = checkField(patterns[match[1]],
						   $(this).val());
			    $(this).next().text(check);
			    if (check) {
				invalidInputs[match[0]] = true;
			    } else {
				delete invalidInputs[match[0]];
			    }
			    if (invalidInputs.isEmpty()) {
				submitButton.removeAttr('disabled');
			    } else {
				submitButton.attr('disabled', 'disabled');
			    }
			});
		    }
		});
	}
    }
}();
