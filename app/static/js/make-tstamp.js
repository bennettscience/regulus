function convertString(dateString) {
    return new Date(dateString).getTime() / 1000;
}

htmx.defineExtension('make-tstamp', {
    onEvent : function(name, evt) {
        // When it's defined, catch the pre-request hook
        if(name === 'htmx:configRequest') {
            // Extract the datestrings and convert them to timestamps
            let request = evt.detail.parameters;

            request.starts = convertString(request.starts);
            request.ends = convertString(request.ends)
        }
    }
  })