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

window.formatDate = formatDate