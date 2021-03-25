var hookWindow = false;

$(function (interact) {
    'use strict';

    // Prevent closing window
    window.onbeforeunload = function() {
        if (hookWindow) {
            return 'Do you want to leave this page? Your progress will not be saved.';
        }
    }

    var imageLength = 100;

    // URL parameters (id & gender)
    var userId, gender, center;
    var parameters = window.location.search.substring(1);
    if (parameters.length > 0) {
        var stuff = parameters.split(/[&=]/);
        userId = stuff[1];
        gender = stuff[3];
        center = stuff[5];
    };

    var experimentId = Date.now();

    // grid
    for (var i = 0; i < 9; ++i) {
        $('#grid').append($('<tr>'));
    }
    $('#grid tr').each(function() {
        for (var i = 0; i < 9; ++i) {
            $(this).append($('<td>'));
        }
    });
    // reset CSS margins in case the screen is not big enough
    var marginLeft = Math.round(1.02 * document.documentElement.clientHeight);
    var minMarginLeft = 9 * imageLength + 30;
    if (marginLeft < minMarginLeft) {
        imageLength = 80;
        minMarginLeft = 9 * imageLength + 30;
        $('#reset').css('margin-left', minMarginLeft.toString() + 'px');
        $('#submit').css('margin-left', minMarginLeft.toString() + 'px');
        $('#reset').css('top', (9 * imageLength - 70).toString() + 'px');
        $('#submit').css('top', (9 * imageLength - 30).toString() + 'px');
        $('#drag-arrow').css('margin-left', (minMarginLeft + 80).toString() + 'px');
        $('#drag-text').css('margin-left', (minMarginLeft + 80).toString() + 'px');
        var dragMarginTop = 3 * imageLength + 50;
        $('#drag-arrow').css('margin-top', dragMarginTop.toString() + 'px');
        $('#drag-text').css('margin-top', dragMarginTop.toString() + 'px');
        $('#images').css('min-width', (minMarginLeft - 10).toString() + 'px');
        $('#images').css('min-height', (minMarginLeft - 10).toString() + 'px');
        $('#grid td').css('width', imageLength.toString() + 'px');
        $('#grid td').css('min-width', imageLength.toString() + 'px');
        $('#grid td').css('height', imageLength.toString() + 'px');
    }
    // reduce area size to contain a 9x9 grid
    $('#dropzone-wrapper').css('width', (9 * imageLength + 9).toString() + 'px');
    $('#dropzone-wrapper').css('height', (9 * imageLength + 9).toString() + 'px');
    // images
    var middleImgName;
    var imgNames = [];
    if (center == 'true') {
        middleImgName = gender + mid_people[userId] + '.jpg';
        for (var i = 1; i < 10; ++i) {
            if (i.toString() != mid_people[userId]) {
                imgNames.push(i.toString());
            }
        }
    } else {
        imgNames = ['1', '2', '3', '4', '5', '6', '7', '8', '9'];
    }
    for (var i = 0; i < imgNames.length; ++i) {
        imgNames[i] = gender + imgNames[i] + '.jpg';
    }
    // shuffle image names
    for (var i = imgNames.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var temp = imgNames[i];
        imgNames[i] = imgNames[j];
        imgNames[j] = temp;
    }
    // append images to DOM
    var marginTop = 20;
    var marginLeft = Math.max(minMarginLeft, Math.round(1.02 * document.documentElement.clientHeight));  // px value of 102vh

    for (var i = 0, img_i = 0; i < 3; ++i) {
        for (var j = 0; j < 3; ++j) {
            if (i == 1 && j == 1 && center == 'true') {
                marginLeft += imageLength + 5;
                continue;
            }
            $('#images').append($('<img>', {
                src: 'img/' + imgNames[img_i],
                class: 'draggable js-drag shadow',
                style: 'margin-left:' + marginLeft.toString() + 'px; margin-top:' + marginTop.toString() + 'px;',
                height: imageLength.toString() + 'px',
                width: imageLength.toString() + 'px',
            }));
            marginLeft += imageLength + 5;
            ++img_i;
        }
        marginTop += imageLength + 5;
        marginLeft = Math.max(minMarginLeft, Math.round(1.02 * document.documentElement.clientHeight));
    }
    // place middle image
    if (center == 'true') {
        var middlePos = $($('#grid td')[40]).position();
        $('#images').append($('<img>', {
            src: 'img/' + middleImgName,
            class: 'draggable js-drag shadow',
            style: 'margin-left:' + middlePos['left'].toString() + 'px; margin-top:' + middlePos['top'].toString() + 'px;',
            height: imageLength.toString() + 'px',
            width: imageLength.toString() + 'px',
        }));
    }
    // image position data
    var numImgDropped = 0;
    var imgDropped = {};
    for (var i = 0; i < imgNames.length; ++i) {
        imgDropped[imgNames[i]] = false;
    }

    // Initialize Firebase
    var config = {
        apiKey: "AIzaSyCv41O7LrglT7ErDtB9itFt5KG5EtyKLfE",
        authDomain: "hierarchy-351e6.firebaseapp.com",
        databaseURL: "https://hierarchy-351e6.firebaseio.com",
        storageBucket: "hierarchy-351e6.appspot.com",
        messagingSenderId: "202596010925"
    };
    firebase.initializeApp(config);

    // reset button
    $('#reset').click(function() {
        hookWindow = false;
        location.reload();
    });
    // submit button
    $('#submit').click(function() {
        if ($('#submit').hasClass('disabled')) {
            return;
        }

        // image positions
        var positions = {}
        $('#images img').each(function() {
            var filename = this.currentSrc.split('/');
            filename = filename[filename.length - 1];
            filename = filename.replace('.', '_');  // because firebase doesn't allow '.' in keys
            positions[filename] = [this.x, this.y];
        });


        // sign in firebase & send data
        firebase.auth().signInAnonymously().then(function(user) {
            var firebaseUid = user.uid;
            console.log('Signed in as ' + firebaseUid);

            firebase.database().ref('/' + userId + '/' + experimentId).set({
                firebase_uid: firebaseUid,
                start_time: startTime,
                gender: gender
            });

            // update results
            var path = '/' + userId + '/' + experimentId;
            var update = {};
            update[path + '/duration'] = (Date.now() - experimentId) / 1000;  // in sec
            update[path + '/end_time'] = (new Date()).toUTCString();
            update[path + '/data'] = positions;

            firebase.database().ref().update(update).then(function() {
                // successful
                hookWindow = false;
                firebase.auth().currentUser.delete();
                // change DOM
                $('#everything').hide();
                $('body').append($('<p>', {
                    text: 'Your response has been recorded. Thank you!',
                    id: 'end-instr'
                }))
            }, function() {
                alert('Error: cannot connect to Firebase');
            });
        }, function() {
            alert('Error: cannot connect to Firebase');
        });
    });

    // interactive.js setup
    var transformProp;
    interact.maxInteractions(Infinity);

    // setup draggable elements
    interact('.js-drag')
        .draggable({
            restrict: {
                restriction: 'parent',
            }
        })
        .inertia(true)
        .on('dragstart', function (event) {
            event.interaction.x = parseInt(event.target.getAttribute('data-x'), 10) || 0;
            event.interaction.y = parseInt(event.target.getAttribute('data-y'), 10) || 0;
        })
        .on('dragmove', function (event) {
            event.interaction.x += event.dx;
            event.interaction.y += event.dy;

            if (transformProp) {
                event.target.style[transformProp] =
                    'translate(' + event.interaction.x + 'px, ' + event.interaction.y + 'px)';
            }
            else {
                event.target.style.left = event.interaction.x + 'px';
                event.target.style.top  = event.interaction.y + 'px';
            }
        })
        .on('dragend', function (event) {
            event.target.setAttribute('data-x', event.interaction.x);
            event.target.setAttribute('data-y', event.interaction.y);
        });

    // setup drop areas.
    // dropzone accepts every draggable
    setupDropzone('#drop', '.js-drag');

    var snapGrid = interact.createSnapGrid({
        x: imageLength,
        y: imageLength,
        offset: { x: $('#drop').offset().top + 4, y: $('#drop').offset().left + 4 }
    });

    /**
     * Setup a given element as a dropzone.
     *
     * @param {HTMLElement|String} el
     * @param {String} accept
     */
    function setupDropzone(el, accept) {
        interact(el)
            .dropzone({
                accept: accept,
                ondropactivate: function (event) {
                    addClass(event.relatedTarget, '-drop-possible');
                },
                ondropdeactivate: function (event) {
                    removeClass(event.relatedTarget, '-drop-possible');
                }
            })
            .on('dropactivate', function (event) {
                var active = event.target.getAttribute('active')|0;

                // change style if it was previously not active
                if (active === 0) {
                    addClass(event.target, '-drop-possible');
                    // event.target.textContent = 'Drop image here';
                }

                event.target.setAttribute('active', active + 1);
            })
            .on('dropdeactivate', function (event) {
                var active = event.target.getAttribute('active')|0;

                // change style if it was previously active
                // but will no longer be active
                if (active === 1) {
                    removeClass(event.target, '-drop-possible');
                    // event.target.textContent = 'Arrange images here';
                }

                event.target.setAttribute('active', active - 1);
            })
            .on('dragenter', function (event) {
                addClass(event.target, '-drop-over');
                // event.relatedTarget.textContent = 'I\'m in';

                interact('.js-drag').draggable({
                    snap: {
                        targets: [snapGrid],
                        relativePoints: [{ x: 0, y: 0 }],
                        endOnly: true
                    }
                })

                // counter
                var filename = event.relatedTarget.currentSrc.split('/');
                filename = filename[filename.length - 1];
                if (!imgDropped[filename]) {
                    imgDropped[filename] = true;
                    ++numImgDropped;
                    if (numImgDropped == imgNames.length && $('#submit').hasClass('disabled')) {
                        $('#submit').removeClass('disabled');
                    }
                }
            })
            .on('dragleave', function (event) {
                removeClass(event.target, '-drop-over');
                // event.relatedTarget.textContent = 'Drag me…';
                interact('.js-drag').draggable({snap: false});

                // counter
                var filename = event.relatedTarget.currentSrc.split('/');
                filename = filename[filename.length - 1];
                if (imgDropped[filename]) {
                    imgDropped[filename] = false;
                    --numImgDropped;
                    if (numImgDropped < imgNames.length && !$('#submit').hasClass('disabled')) {
                        $('#submit').addClass('disabled');
                    }
                }
            })
            .on('drop', function (event) {
                removeClass(event.target, '-drop-over');
                // event.relatedTarget.textContent = 'Dropped';
            });
    }

    function addClass (element, className) {
        if (element.classList) {
            return element.classList.add(className);
        }
        else {
            element.className += ' ' + className;
        }
    }

    function removeClass (element, className) {
        if (element.classList) {
            return element.classList.remove(className);
        }
        else {
            element.className = element.className.replace(new RegExp(className + ' *', 'g'), '');
        }
    }

    interact(document).on('ready', function () {
        transformProp = 'transform' in document.body.style
            ? 'transform': 'webkitTransform' in document.body.style
            ? 'webkitTransform': 'mozTransform' in document.body.style
            ? 'mozTransform': 'oTransform' in document.body.style
            ? 'oTransform': 'msTransform' in document.body.style
            ? 'msTransform': null;
    });

    hookWindow = true;
    var startTime = (new Date()).toUTCString();

}(window.interact));
