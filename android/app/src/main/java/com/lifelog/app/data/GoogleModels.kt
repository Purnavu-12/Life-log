package com.lifelog.app.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class GoogleStatus(
    val connected: Boolean = false,
    val email: String? = null,
    val scopes: List<String> = emptyList(),
)

@Serializable
data class GoogleCalendar(
    val id: String,
    val summary: String? = null,
    val primary: Boolean = false,
)

@Serializable
data class CalendarsResponse(val calendars: List<GoogleCalendar> = emptyList())

@Serializable
data class GoogleEventTime(
    val dateTime: String? = null,
    val date: String? = null,
)

@Serializable
data class GoogleEvent(
    val id: String,
    val summary: String? = null,
    val start: GoogleEventTime? = null,
    val end: GoogleEventTime? = null,
    val location: String? = null,
    val description: String? = null,
)

@Serializable
data class GoogleEventsResponse(val events: List<GoogleEvent> = emptyList())

@Serializable
data class GmailHeader(
    val name: String? = null,
    val value: String? = null,
)

@Serializable
data class GmailPayload(
    val headers: List<GmailHeader> = emptyList(),
)

@Serializable
data class GmailMessage(
    val id: String,
    val threadId: String? = null,
    val snippet: String? = null,
    val payload: GmailPayload? = null,
)

@Serializable
data class GoogleMessagesResponse(val messages: List<GmailMessage> = emptyList())

@Serializable
data class GoogleProfileData(
    @SerialName("emailAddress") val emailAddress: String? = null,
    @SerialName("messagesTotal") val messagesTotal: Int? = null,
)

@Serializable
data class GoogleProfileResponse(val profile: GoogleProfileData? = null)

@Serializable
data class SimpleResponse(val success: Boolean = false, val message: String? = null)

fun GmailMessage.subject(): String? =
    payload?.headers?.firstOrNull { it.name?.equals("Subject", ignoreCase = true) == true }?.value

fun GmailMessage.from(): String? =
    payload?.headers?.firstOrNull { it.name?.equals("From", ignoreCase = true) == true }?.value