package com.lifelog.app.data

import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive

/** A memory as returned by `/api/memories` (leniently parsed). */
data class Memory(
    val id: String,
    val vectorId: String? = null,
    val transcript: String = "",
    val summary: String? = null,
    val sentiment: String? = null,
    val tags: List<String> = emptyList(),
    val tasks: List<String> = emptyList(),
    val people: List<String> = emptyList(),
    val date: String? = null,
    val time: String? = null,
) {
    val content: String get() = transcript
    val title: String get() = summary?.takeIf { it.isNotBlank() } ?: transcript.take(80)
}

object MemoryParser {
    fun parse(root: kotlinx.serialization.json.JsonElement): List<Memory> =
        Lenient.objectList(root, "memories", "results", "items").map { obj ->
            val id = Lenient.str(obj, "id", "vector_id", "memory_id")
                ?: Lenient.long(obj, "id")?.toString()
                ?: ""
            val created = Lenient.double(obj, "created_at", "timestamp")
            val transcript = Lenient.str(obj, "transcript", "content", "text") ?: ""
            Memory(
                id = id,
                vectorId = Lenient.str(obj, "vector_id"),
                transcript = transcript,
                summary = Lenient.str(obj, "summary"),
                sentiment = Lenient.str(obj, "sentiment"),
                tags = Lenient.stringList(obj, "tags"),
                tasks = Lenient.stringList(obj, "tasks"),
                people = Lenient.stringList(obj, "people"),
                date = Lenient.str(obj, "date") ?: created?.let { epochToDate(it) },
                time = Lenient.str(obj, "time") ?: created?.let { epochToTime(it) },
            )
        }

    private fun epochToDate(epoch: Double): String {
        val millis = (epoch * 1000).toLong()
        return java.time.Instant.ofEpochMilli(millis)
            .atZone(java.time.ZoneId.systemDefault())
            .toLocalDate()
            .toString()
    }

    private fun epochToTime(epoch: Double): String {
        val millis = (epoch * 1000).toLong()
        return java.time.Instant.ofEpochMilli(millis)
            .atZone(java.time.ZoneId.systemDefault())
            .toLocalTime()
            .toString().take(5)
    }
}

/** A semantic-search result. */
data class SearchResult(
    val id: String,
    val text: String,
    val similarity: Double = 0.0,
    val summary: String? = null,
    val tags: List<String> = emptyList(),
    val date: String? = null,
)

object SearchParser {
    fun parse(root: kotlinx.serialization.json.JsonElement): List<SearchResult> =
        Lenient.objectList(root, "results", "memories", "items").map { obj ->
            val metadata = obj["metadata"] as? JsonObject
            SearchResult(
                id = Lenient.str(obj, "id") ?: Lenient.long(obj, "id")?.toString() ?: "",
                text = Lenient.str(obj, "text", "content", "transcript")
                    ?: metadata?.let { Lenient.str(it, "text", "content", "transcript") }
                    ?: "",
                similarity = Lenient.double(obj, "similarity", "score") ?: 0.0,
                summary = Lenient.str(obj, "summary") ?: metadata?.let { Lenient.str(it, "summary") },
                tags = Lenient.stringList(obj, "tags").ifEmpty {
                    metadata?.let { Lenient.stringList(it, "tags") } ?: emptyList()
                },
                date = Lenient.str(obj, "date") ?: metadata?.let { Lenient.str(it, "date") },
            )
        }
}

/** Google account connection status. */
data class GoogleStatus(
    val connected: Boolean = false,
    val email: String? = null,
    val scopes: List<String> = emptyList(),
)

object GoogleStatusParser {
    fun parse(root: kotlinx.serialization.json.JsonElement): GoogleStatus {
        val obj = root as? JsonObject ?: return GoogleStatus()
        return GoogleStatus(
            connected = Lenient.bool(obj, "connected") ?: false,
            email = Lenient.str(obj, "email", "emailAddress", "email_address"),
            scopes = Lenient.stringList(obj, "scopes"),
        )
    }
}

/** A Google calendar the account can read. */
data class CalendarInfo(
    val id: String = "",
    val summary: String = "",
    val primary: Boolean = false,
)

object CalendarListParser {
    fun parse(root: kotlinx.serialization.json.JsonElement): List<CalendarInfo> =
        Lenient.objectList(root, "calendars", "items", "results").map { obj ->
            CalendarInfo(
                id = Lenient.str(obj, "id") ?: "",
                summary = Lenient.str(obj, "summary", "name") ?: "",
                primary = Lenient.bool(obj, "primary") ?: false,
            )
        }
}

/** A calendar event. */
data class CalendarEvent(
    val id: String = "",
    val summary: String = "",
    val start: String? = null,
    val end: String? = null,
    val location: String? = null,
    val description: String? = null,
    val calendar: String? = null,
) {
    /** Start as an instant, or null for all-day events (date-only values). */
    val startInstant: java.time.Instant?
        get() = parseEventInstant(start)

    val allDay: Boolean
        get() = start != null && start.length == 10
}

/** Parses an RFC3339 timestamp, or an all-day `YYYY-MM-DD` date. */
fun parseEventInstant(value: String?): java.time.Instant? {
    if (value.isNullOrBlank()) return null
    return runCatching { java.time.Instant.parse(value) }.getOrNull()
        ?: runCatching { java.time.OffsetDateTime.parse(value).toInstant() }.getOrNull()
        ?: runCatching {
            java.time.LocalDate.parse(value)
                .atStartOfDay(java.time.ZoneId.systemDefault())
                .toInstant()
        }.getOrNull()
}

object CalendarEventParser {
    fun parse(root: kotlinx.serialization.json.JsonElement): List<CalendarEvent> =
        Lenient.objectList(root, "events", "items", "upcoming").map { obj ->
            val start = obj["start"]
            val end = obj["end"]
            CalendarEvent(
                id = Lenient.str(obj, "id") ?: "",
                summary = Lenient.str(obj, "summary", "title") ?: "",
                start = timeValue(start),
                end = timeValue(end),
                location = Lenient.str(obj, "location"),
                description = Lenient.str(obj, "description"),
            )
        }

    private fun timeValue(element: kotlinx.serialization.json.JsonElement?): String? {
        if (element == null) return null
        val obj = element as? JsonObject
        if (obj != null) {
            Lenient.str(obj, "dateTime", "date_time", "date")?.let { return it }
        }
        val primitive = element as? JsonPrimitive
        return primitive?.content
    }
}

/** A Gmail message. */
data class GmailMessage(
    val id: String = "",
    val subject: String = "",
    val sender: String = "",
    val snippet: String = "",
)

object GmailParser {
    fun parse(root: kotlinx.serialization.json.JsonElement): List<GmailMessage> =
        Lenient.objectList(root, "messages", "items", "results").map { obj ->
            val payload = obj["payload"] as? JsonObject
            val headers = payload?.get("headers") as? kotlinx.serialization.json.JsonArray
            fun header(name: String): String? {
                headers?.forEach { entry ->
                    val header = entry as? JsonObject ?: return@forEach
                    val key = Lenient.str(header, "name") ?: return@forEach
                    if (key.equals(name, ignoreCase = true)) {
                        Lenient.str(header, "value")?.let { return it }
                    }
                }
                return null
            }
            GmailMessage(
                id = Lenient.str(obj, "id") ?: "",
                subject = header("Subject") ?: Lenient.str(obj, "subject") ?: "(No subject)",
                sender = header("From") ?: Lenient.str(obj, "from", "sender") ?: "",
                snippet = Lenient.str(obj, "snippet", "text") ?: "",
            )
        }
}

/** A proposed action (TODO). */
data class ActionItem(
    val id: String = "",
    val memoryId: String? = null,
    val title: String = "",
    val description: String? = null,
    val actionType: String? = null,
    val priority: String? = null,
    val status: String? = null,
    val confidence: Double? = null,
)

object ActionParser {
    fun parse(root: kotlinx.serialization.json.JsonElement): List<ActionItem> =
        Lenient.objectList(root, "actions", "items", "results").map { obj ->
            ActionItem(
                id = Lenient.str(obj, "id") ?: Lenient.long(obj, "id")?.toString() ?: "",
                memoryId = Lenient.str(obj, "memory_id", "memoryId"),
                title = Lenient.str(obj, "title", "summary") ?: "",
                description = Lenient.str(obj, "description"),
                actionType = Lenient.str(obj, "action_type", "actionType", "type"),
                priority = Lenient.str(obj, "priority"),
                status = Lenient.str(obj, "status"),
                confidence = Lenient.double(obj, "confidence"),
            )
        }
}

/** Live server / device status from `/status`. */
data class ServerStatus(
    val connectedClients: Int = 0,
    val connectedDevices: Int = 0,
    val recording: Boolean = false,
    val activeSession: String? = null,
    val queueSize: Int = 0,
)

object StatusParser {
    fun parse(root: kotlinx.serialization.json.JsonElement): ServerStatus {
        val obj = root as? JsonObject ?: return ServerStatus()
        return ServerStatus(
            connectedClients = Lenient.long(obj, "connected_clients", "connected_event_clients")?.toInt() ?: 0,
            connectedDevices = Lenient.long(obj, "connected_devices", "connected_audio_devices")?.toInt() ?: 0,
            recording = Lenient.bool(obj, "recording") ?: false,
            activeSession = Lenient.str(obj, "active_session", "active_sessions"),
            queueSize = Lenient.long(obj, "queue_size", "queue_depth")?.toInt() ?: 0,
        )
    }
}

/** The daily briefing, flattened for the Today screen. */
data class DailyBriefing(
    val memories: List<Memory> = emptyList(),
    val calendar: List<CalendarEvent> = emptyList(),
    val importantEmails: List<GmailMessage> = emptyList(),
    val actions: List<ActionItem> = emptyList(),
    val totalMemories: Int = 0,
    val pendingActions: Int = 0,
)

object BriefingParser {
    fun parse(root: kotlinx.serialization.json.JsonElement): DailyBriefing {
        val obj = root as? JsonObject ?: return DailyBriefing()
        val memories = MemoryParser.parse(obj["memories"] ?: kotlinx.serialization.json.JsonArray(emptyList()))
        val calendar = CalendarEventParser.parse(obj["calendar"] ?: kotlinx.serialization.json.JsonArray(emptyList()))
        val emails = GmailParser.parse(obj["important_emails"] ?: obj["gmail"] ?: kotlinx.serialization.json.JsonArray(emptyList()))
        val actions = ActionParser.parse(obj["actions"] ?: kotlinx.serialization.json.JsonArray(emptyList()))
        return DailyBriefing(
            memories = memories,
            calendar = calendar,
            importantEmails = emails,
            actions = actions,
            totalMemories = Lenient.long(obj, "total_memories")?.toInt() ?: memories.size,
            pendingActions = Lenient.long(obj, "pending_actions", "total_pending_actions")?.toInt()
                ?: actions.count { it.status == "pending" },
        )
    }
}
