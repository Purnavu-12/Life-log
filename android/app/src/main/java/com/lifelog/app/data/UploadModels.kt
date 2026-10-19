package com.lifelog.app.data

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject

@Serializable
data class ChatRequest(val question: String)

data class ChatResponse(
    val answer: String = "",
    val sources: List<SearchResult> = emptyList(),
)

/** The structured information the server extracts from a transcript. */
data class Extracted(
    val summary: String? = null,
    val sentiment: String? = null,
    val tags: List<String> = emptyList(),
    val topics: List<String> = emptyList(),
    val tasks: List<String> = emptyList(),
    val people: List<String> = emptyList(),
    val dates: List<String> = emptyList(),
    val actionItems: List<String> = emptyList(),
)

/** A proposed action (TODO) returned after an upload. */
data class ProposedAction(
    val id: String = "",
    val title: String = "",
    val description: String? = null,
    val actionType: String? = null,
    val priority: String? = null,
    val status: String? = null,
    val confidence: Double? = null,
)

/** The result of uploading audio to `/api/upload`. */
data class UploadResponse(
    val success: Boolean = false,
    val memoryId: String? = null,
    val databaseId: String? = null,
    val transcript: String? = null,
    val extracted: Extracted? = null,
    val proposedActions: List<ProposedAction> = emptyList(),
    val actionCount: Int = 0,
    val detail: String? = null,
    val error: String? = null,
)

object UploadParser {
    fun parse(root: JsonElement): UploadResponse {
        val obj = root as? JsonObject ?: return UploadResponse()
        val extractedObj = obj["extracted"] as? JsonObject
        val extracted = extractedObj?.let {
            Extracted(
                summary = Lenient.str(it, "summary"),
                sentiment = Lenient.str(it, "sentiment"),
                tags = Lenient.stringList(it, "tags"),
                topics = Lenient.stringList(it, "topics"),
                tasks = Lenient.stringList(it, "tasks"),
                people = Lenient.stringList(it, "people"),
                dates = Lenient.stringList(it, "dates"),
                actionItems = Lenient.stringList(it, "action_items", "actionItems"),
            )
        }
        val actions = Lenient.objectList(obj["proposed_actions"] ?: kotlinx.serialization.json.JsonArray(emptyList())).map {
            ProposedAction(
                id = Lenient.str(it, "id") ?: Lenient.long(it, "id")?.toString() ?: "",
                title = Lenient.str(it, "title") ?: "",
                description = Lenient.str(it, "description"),
                actionType = Lenient.str(it, "action_type", "actionType"),
                priority = Lenient.str(it, "priority"),
                status = Lenient.str(it, "status"),
                confidence = Lenient.double(it, "confidence"),
            )
        }
        return UploadResponse(
            success = Lenient.bool(obj, "success") ?: false,
            memoryId = Lenient.str(obj, "memory_id", "memoryId"),
            databaseId = Lenient.str(obj, "database_id", "databaseId") ?: Lenient.long(obj, "database_id", "databaseId")?.toString(),
            transcript = Lenient.str(obj, "transcript", "text"),
            extracted = extracted,
            proposedActions = actions,
            actionCount = Lenient.long(obj, "action_count", "actionCount")?.toInt() ?: actions.size,
            detail = Lenient.str(obj, "detail"),
            error = Lenient.str(obj, "error"),
        )
    }
}

/** Parses the chat response, accepting both string and object answers. */
object ChatParser {
    fun parse(root: JsonElement): ChatResponse {
        val obj = root as? JsonObject ?: return ChatResponse()
        val answer = Lenient.str(obj, "answer", "response", "reply", "message") ?: ""
        val sources = SearchParser.parse(obj["sources"] ?: kotlinx.serialization.json.JsonArray(emptyList()))
        return ChatResponse(answer = answer, sources = sources)
    }
}
