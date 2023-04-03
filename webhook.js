/**
 * Google Apps Script webhook sample
 * (c) 2022 Brian Bennett - ohheybrian.com
 *
 * Details on using a Google Apps Scipt webhook can be found here:
 * https://blog.ohheybrian.com/2021/09/using-google-apps-script-as-a-webhook/
 *
 */
const accessKey = 'set_your_access_key_here'
const setup = () => { return true }

/**
 * Handle a POST request to add a user to a calendar event from the application
 *
 * @param String method - the action to perform
 * @param String token - access token from the request
 * @param String userId - Valid user email address
 * @param String calendarId - Valid Google Calendar ID
 * @param STring eventID - Valid Google Calendar event ID
 */
function doPost(e) {
  let result;
  // Get the contents of the request
  let params = JSON.parse(e.postData.contents)

  let method = params.method;
  let token = params.token;
  let userIds = params.userIds;
  let calendarId = params.calendarId;
  let eventId = params.eventId;
  let body = params.body;

  Logger.log(method)
  Logger.log(body)

  if(token === accessKey) {
    if(method === 'post') {
      result = createEvent(calendarId, body)
    } else if(method === 'patch' || method === 'pop') {
      result = userRegistration(userIds, calendarId, eventId, method)
    } else if(method === 'put') {
      result = updateEvent(calendarId, eventId, body)
    }else if(method === 'delete') {
      result = deleteEvent(calendarId, eventId)
    }
  } else {
    result = {'status': 'Forbidden', 'message': 'You do not have access to this resource.', 'statusCode': 403}
  }
  return ContentService.createTextOutput(JSON.stringify(result))
}

function getEvent(calendarId, eventId) {
  let event = Calendar.Events.get(calendarId, eventId)
  return event;
}

function createEvent(calendarId, body) {
  let args = {"sendUpdates": "all"}
  if(body.hasOwnProperty('conferenceData')) {
    args["conferenceDataVersion"] = 1
  }
  try {
    const calendar = Calendar.Events.insert(body, calendarId, args)
    return calendar;
  } catch(e) {
    Logger.log(e)
  }
}

function deleteEvent(calendarId, eventId) {
  const event = Calendar.Events.remove(calendarId, eventId, {sendUpdates: 'all'})
  return event;
}

function updateEvent(calendarId, eventId, body) {
  Logger.log(body.conferenceDataVersion)
  let event = Calendar.Events.patch(body, calendarId, eventId, {sendUpdates: 'all', conferenceDataVersion: body.conferenceDataVersion})

  return event;
}

function userRegistration(userIds, calendarId, eventId, method) {
  let resource;

  Logger.log(userIds)

  let event = Calendar.Events.get(calendarId, eventId)
  let attendees = event.attendees;

  // Add an attendee to the event
  if(method === 'patch') {
    if(attendees) {
      attendees = event.attendees.concat(userIds)
      resource = { "attendees": attendees}
    } else {
      resource = {
        attendees: userIds
      }
    }
  } else if(method === 'pop') {
    // Remove a user from the invitation to the event
    let filtered = event.attendees.filter(user => user.email !== userId);
    resource = {
      "attendees": filtered
    }
  }

  try {
    Calendar.Events.patch(
      resource,
      calendarId,
      eventId,
      {sendUpdates: 'all'}
    )
    return {'status': 'OK', 'statusCode': 200, 'message': 'The event was updated successfully.'}
  } catch(e) {
    Logger.log(e)
    return {'status': 'Error', 'messages': e, 'statusCode': 500}
  }
}
