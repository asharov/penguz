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
    function padNumberWithZero (number) {
	return (number < 10 ? "0" : "") + number;
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
	}
    }
}();
