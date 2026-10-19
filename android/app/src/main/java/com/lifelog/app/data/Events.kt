package com.lifelog.app.data

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.util.UUID

/**
 * A message received on the `/events` WebSocket.
 * Contract types: device_connected, recording_started, transcript, recording_finished.
 */
data class LiveEvent(
    val id: String = UUID.randomUUID().toString(),
    val receivedAt: Long = System.currentTimeMillis(),
    val type: String = "transcript",
    val text: String,
    val sessionId: String? = null,
    val deviceId: String? = null,
    val sequence: Long? = null,
    val isFinal: Boolean? = null,
    val raw: String,
) {
    val isTranscript: Boolean get() = type == "transcript"
    val isStatus: Boolean get() = !isTranscript
}

object LiveEventParser {
    private val json = Json { ignoreUnknownKeys = true; isLenient = true }

    fun parse(message: String): LiveEvent {
        return try {
            val element = json.parseToJsonElement(message)
            val obj = element as? JsonObject
            if (obj == null) {
                LiveEvent(text = message, raw = message)
            } else {
                val type = Lenient.str(obj, "type") ?: "transcript"
                val text = Lenient.str(obj, "text", "transcript", "content", "summary", "message")
                    ?: when (type) {
                        "device_connected" -> "Device connected: ${Lenient.str(obj, "device_name") ?: Lenient.str(obj, "device_id") ?: "unknown device"}"
                        "recording_started" -> "Recording started"
                        "recording_finished" -> "Recording finished (${Lenient.str(obj, "duration_ms") ?: "?"} ms)"
                        else -> message
                    }
                LiveEvent(
                    type = type,
                    text = text,
                    sessionId = Lenient.str(obj, "session_id", "sessionId"),
                    deviceId = Lenient.str(obj, "device_id", "deviceId"),
                    sequence = Lenient.long(obj, "sequence"),
                    isFinal = Lenient.bool(obj, "is_final", "isFinal"),
                    raw = message,
                )
            }
        } catch (e: Exception) {
            LiveEvent(text = message, raw = message)
        }
    }
}
