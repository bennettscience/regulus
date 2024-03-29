function makeQuill(el, placeholder) {
    const toolbarOptions = [
        [{'header': [1, 2, false]}],
        ['bold', 'italic', 'underline'],
        [{'list': 'ordered'}, {'list': 'bullet'}]
    ]

    let quill = new Quill(el, {
        theme: 'snow',
        placeholder: placeholder,
        modules: {
            toolbar: toolbarOptions,
            clipboard: {
                matchVisual: false
            }
        },
    })

    window.quill = quill
}

// Set the initial value of the Quill editor if a description exists
function setInitial(text) {
    const delta = quill.clipboard.convert(text)
    quill.setContents(delta, 'silent')
}

function formatDate(target, dateStr) {

    const formatted_date = new Date(dateStr)

    const formats = {
        dateOnly: {
            year: 'numeric',
            month: 'numeric',
            day: 'numeric'
        },
        starts: {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: 'numeric',
            minute: 'numeric',
        },
        ends: {
            hour: 'numeric',
            minute: 'numeric',
        }
    }

    return new Intl.DateTimeFormat('en', formats[target]).format(formatted_date)
}

function shiftISOTime(datetime) {
    let today = new Date(datetime);
    let timeZone = today.getTimezoneOffset() * 60 * 1000;
    let local = today - timeZone;
    let localDate = new Date(local).toISOString();
    return localDate.slice(0, -8);
}

function showToast(msg = 'Processing...', timeout = 5000, err = false) {
    const toast = document.querySelector(`#toast`)
    // Handle message objects from hyperscript
    // For non-template returns, the backend will also return JSON with
    // the `message` key with details for the user.
    if(typeof msg === 'object') {
        // HTMX returns strings, so convert it to an object
        let obj = JSON.parse(msg.xhr.responseText)
        msg = obj.message
    }

    toast.children[0].innerText = msg;
    if(err) {
        toast.classList.add('error')
    }
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show')
        toast.children[0].innerText = 'Processing...'
        if(err) {
            toast.classList.remove('error')
        }
    }, timeout)
}

function cancelToast() {
    const toast = document.querySelector(`#toast`)
    toast.classList.remove('show');
    toast.children[0].innerText = 'Processing...'
    clearTimeout()
}

// Listen for toast messaging from the server
htmx.on('showToast', evt => {
    showToast(evt.detail.value)
})

document.addEventListener('htmx:afterSwap', (evt) => {
    const pathInfo = evt.detail.pathInfo;

    if(pathInfo.path.includes('edit') || pathInfo.path.includes('copy')) {
        makeQuill("#editor", "Enter event description")
    }

    if(pathInfo.path === '/create') {
        makeQuill("#editor", "Enter event description")
    }
})

// document.addEventListener('htmx:afterRequest', (evt) => {
//     console.log(evt)
// })

// document.addEventListener('htmx:responseError', (evt) => {
//     console.log(evt)
//     showToast(evt.detail.xhr.responseText, true)
// })

// document.addEventListener('htmx:beforeSend', function(evt) {
//     console.info('Dispatched...')
//     console.info(evt.detail)
// })

window.cancelToast = cancelToast
window.formatDate = formatDate
window.makeQuill = makeQuill
window.setInitial = setInitial
window.shiftISOTime = shiftISOTime
window.showToast = showToast
