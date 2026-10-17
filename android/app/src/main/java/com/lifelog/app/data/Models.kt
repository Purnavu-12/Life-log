package com.lifelog.app.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Memory(
    val id: String,
    val date: String? = null,
    val time: String? = null,
    val content: String,
    val summary: String? = null,
    val sentiment: String? = null,
    val tags: List<String> = emptyList(),
    val tasks: List<String> = emptyList(),
    val people: List<String> = emptyList(),
)

@Serializable
data class MemoriesResponse(val memories: List<Memory> = emptyList())

@Serializable
data class Extracted(
    val summary: String? = null,
    val tasks: List<String> = emptyList(),
    val people: List<String> = emptyList(),
    val dates: List<String> = emptyList(),
    val topics: List<String> = emptyList(),
    val tags: List<String> = emptyList(),
    val sentiment: String? = null,
    @SerialName("action_items") val actionItems: List<String> = emptyList(),
)

@Serializable
data class UploadResponse(
    val success: Boolean = false,
    val memory_id: String? = null,
    val transcript: String? = null,
    val extracted: Extracted? = null,
    val detail: String? = null,
    val error: String? = null,
)

@Serializable
data class SearchResult(
    val id: String,
    val date: String? = null,
    val similarity: Double = 0.0,
    val content: String,
    val summary: String? = null,
    val tags: List<String> = emptyList(),
)

@Serializable
data class SearchResponse(val results: List<SearchResult> = emptyList())
