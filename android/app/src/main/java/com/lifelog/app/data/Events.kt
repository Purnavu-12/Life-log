package com.lifelog.app.data

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.util.UUID

data class LiveEvent(
    val id: String = UUID.randomUUID().toString(),
    val receivedAt: Long = System.currentTimeMillis(),
    val text: String,
    val raw: String,
)

object EventParser {
    private val json = Json { ignoreUnknownKeys = true }

    fun parse(message: String): LiveEvent {
        val extracted = try {
            val element = json.parseToJsonElement(message)
            val obj = element as? JsonObject
            obj?.let {
                it["transcript"]?.jsonPrimitive?.content
                    ?: it["text"]?.jsonPrimitive?.content
                    ?: it["content"]?.jsonPrimitive?.content
                    ?: it["summary"]?.jsonPrimitive?.content
                    ?: it["message"]?.jsonPrimitive?.content
                    ?: it["transcription"]?.jsonPrimitive?.content
            } ?: message
        } catch (e: Exception) {
            message
        }
        return LiveEvent(text = extracted, raw = message)
    }
}