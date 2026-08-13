(function() {
'use strict';
var besogo = window.besogo = window.besogo || {}; // Establish our namespace
besogo.VERSION = '0.0.2-alpha';

besogo.create = function(container, options) {
    var editor, // Core editor object
        boardDiv; // Board display container

    container.className += ' besogo-container'; // Marks this div as initialized

    // Process the board-only options used by the site wrapper
    options = options || {}; // Makes option checking simpler
    options.size = besogo.parseSize(options.size || 19);
    options.coord = options.coord || 'none';
    options.tool = options.tool || 'auto';
    if (options.shadows === undefined) {
        options.shadows = 'auto';
    } else if (options.shadows === 'off') {
        options.shadows = false;
    }

    // Make the core editor object
    editor = besogo.makeEditor(options.size.x, options.size.y);
    container.besogoEditor = editor;
    editor.setTool(options.tool);
    editor.setCoordStyle(options.coord);
    if (options.realstones) { // Using realistic stones
        editor.REAL_STONES = true;
        editor.SHADOWS = options.shadows;
    } else { // SVG stones
        editor.SHADOWS = (options.shadows && options.shadows !== 'auto');
    }

    if (!options.nokeys) { // Add keypress handler unless nokeys option is truthy
        addKeypressHandler(container, editor);
    }

    if (typeof options.variants === 'number' || typeof options.variants === 'string') {
        editor.setVariantStyle(+options.variants); // Converts to number
    }

    while (container.firstChild) { // Remove all children of container
        container.removeChild(container.firstChild);
    }

    boardDiv = document.createElement('div');
    boardDiv.className = 'besogo-board';
    container.appendChild(boardDiv);
    besogo.makeBoardDisplay(boardDiv, editor); // Create board display
}; // END function besogo.create

// Parses size parameter from SGF format
besogo.parseSize = function(input) {
    var matches,
        sizeX,
        sizeY;

    input = (input + '').replace(/\s/g, ''); // Convert to string and remove whitespace

    matches = input.match(/^(\d+):(\d+)$/); // Check for #:# pattern
    if (matches) { // Composed value pattern found
        sizeX = +matches[1]; // Convert to numbers
        sizeY = +matches[2];
    } else if (input.match(/^\d+$/)) { // Check for # pattern
        sizeX = +input; // Convert to numbers
        sizeY = +input; // Implied square
    } else { // Invalid input format
        sizeX = sizeY = 19; // Default size value
    }
    if (sizeX > 52 || sizeX < 1 || sizeY > 52 || sizeY < 1) {
        sizeX = sizeY = 19; // Out of range, set to default
    }

    return { x: sizeX, y: sizeY };
};

// Sets up keypress handling
function addKeypressHandler(container, editor) {
    if (!container.getAttribute('tabindex')) {
        container.setAttribute('tabindex', '0'); // Set tabindex to allow div focusing
    }

    container.addEventListener('keydown', function(evt) {
        evt = evt || window.event;
        switch (evt.keyCode) {
            case 33: // page up
                editor.prevNode(10);
                break;
            case 34: // page down
                editor.nextNode(10);
                break;
            case 35: // end
                editor.nextNode(-1);
                break;
            case 36: // home
                editor.prevNode(-1);
                break;
            case 37: // left
                if ( evt.shiftKey ) {
                    editor.prevBranchPoint();
                } else {
                    editor.prevNode(1);
                }
                break;
            case 38: // up
                editor.nextSibling(-1);
                break;
            case 39: // right
                editor.nextNode(1);
                break;
            case 40: // down
                editor.nextSibling(1);
                break;
            case 46: // delete
                editor.cutCurrent();
                break;
        } // END switch (evt.keyCode)
        if (evt.keyCode >= 33 && evt.keyCode <= 40) {
            evt.preventDefault(); // Suppress page nav controls
        }
    }); // END func() and addEventListener
} // END function addKeypressHandler

})(); // END closure
