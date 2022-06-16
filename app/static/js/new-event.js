function convertString(dateString) {
    return new Date(dateString).getTime() / 1000;
}

function getDescription() {
    return quill.root.innerHTML;
}

// Handle params for creating a new event. This is necessary to 
// convert JS timestamps into Python timestamps and to extract
// the description from the Quill editor.
htmx.defineExtension('new-event', {
    onEvent : function(name, evt) {
        // When it's defined, catch the pre-request hook
        if(name === 'htmx:configRequest') {
            // Extract the datestrings and convert them to timestamps
            let request = evt.detail.parameters;

            request.starts = convertString(request.starts);
            request.ends = convertString(request.ends)
            request.description = getDescription()
            evt.detail.headers['Content-Type'] = 'application/json'
        }
    },
    encodeParameters : function(xhr, parameters, elt) {
        xhr.overrideMimeType('text/json');
        return (JSON.stringify(parameters));
    }
  })