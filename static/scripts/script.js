
var FRONT = 0
var BACK = 1

var state = {
	side: FRONT,
	card: null,
	nextCard: null
}

class Swipe {
    constructor(element) {
        this.xDown = null;
        this.yDown = null;
        this.element = typeof(element) === 'string' ? document.querySelector(element) : element;
        this.element.addEventListener('touchstart', function(evt) {
            this.xDown = evt.touches[0].clientX;
            this.yDown = evt.touches[0].clientY;
        }.bind(this), false);

    }

    onLeft(callback) {
        this.onLeft = callback;

        return this;
    }

    onRight(callback) {
        this.onRight = callback;

        return this;
    }

    onUp(callback) {
        this.onUp = callback;

        return this;
    }

    onDown(callback) {
        this.onDown = callback;

        return this;
    }

    handleTouchMove(evt) {
        if ( ! this.xDown || ! this.yDown ) {
            return;
        }

        var xUp = evt.touches[0].clientX;
        var yUp = evt.touches[0].clientY;

        this.xDiff = this.xDown - xUp;
        this.yDiff = this.yDown - yUp;

        if ( Math.abs( this.xDiff ) > Math.abs( this.yDiff ) ) { // Most significant.
            if ( this.xDiff > 0 ) {
                this.onLeft();
            } else {
                this.onRight();
            }
        } else {
            if ( this.yDiff > 0 ) {
                this.onUp();
            } else {
                this.onDown();
            }
        }

        // Reset values.
        this.xDown = null;
        this.yDown = null;
    }

    run() {
        this.element.addEventListener('touchmove', function(evt) {
            this.handleTouchMove(evt).bind(this);
        }.bind(this), false);
    }
}

$(document).ready(function() {
	changeButtons()
	getNextCard()
	displayFront()
	var swiper = new Swipe("#cardArea")
	swiper.onLeft(leftSwipe)
	swiper.onRight(rightSwipe)
	swiper.run()
})

function leftSwipe() {
	if (state.side == FRONT) {
		flip()
	} else {
		markIncorrect()
	}
}

function rightSwipe() {
	if (state.side == FRONT) {
		flip()
	} else {
		markCorrect()
	}
}

function sendScore(id, score) {
	$.ajax({
		type: 'POST',
		url: '/api/sendScore',
		data: JSON.stringify({
            id: id,
			score: score
		}),
		contentType: "application/json; charset=utf-8",
		dataType: 'json'
	})
}

function getNextCard() {
	if (!state.card) {
		getCard()
		state.card = state.nextCard
		state.nextCard = null
	}
	getCard()
}

function getCard() {
	$.ajax({
		type: 'GET',
		url: '/api/getCard',
		async: false,
		success: function(data) {
			state.nextCard = data
		},
		error: function() {
			console.log("Error getting card. Trying again.")
			// getCard()
		}
	})
}

function flip() {
	if (state.side == FRONT) {
		displayBack()
		state.side = BACK
	} else {
		clearBack()
		displayNextFront()
		getNextCard()
		state.side = FRONT
	}
	changeButtons()
}

function changeButtons() {
	if (state.side == FRONT) {
		$('#correctButton').addClass('hidden')
		$('#incorrectButton').addClass('hidden')
		$('#flipButton').removeClass('hidden')
	} else {
		$('#correctButton').removeClass('hidden')
		$('#incorrectButton').removeClass('hidden')
		$('#flipButton').addClass('hidden')
	}
}

function displayFront() {
	// $('#front').html("<iframe src='https://github.com/anars/blank-audio/blob/master/250-milliseconds-of-silence.mp3' id='silence' type='audio.mp3' style='display:none' allow='autoplay'></iframe><audio autoplay><source src='/static/audio/" + state.card.audio + "' type='audio/mp3'></audio><p class='cardText'>" + state.card.front + "</p>")
	$('#front').html(/*"<audio controls autoplay id='frontAudio'><source src='/static/audio/" + state.card.audio + "' type='audio/mp3'></audio>*/"<p class='cardText'>" + state.card.front + "</p>")
	//$('#frontAudio')[0].play()
}

function displayBack() {
	$('#back').html("<p class='cardText'>" + state.card.back + "</p><p class='cardScore'>" + state.card.score + " / " + state.card.maxScore  + "</p>")
}

function clearFront() {
	$('#functionront').html("")
}

function clearBack() {
	$('#back').html("")
}

function displayNextFront() {
	clearFront()
	state.card = state.nextCard
	state.nextCard = null
	displayFront()
}

function markCorrect() {
	sendScore(state.card.id, -1)
	flip()
}

function markIncorrect() {
	sendScore(state.card.id, 1)
	flip()
}
