package com.lifelog.app.ui

import android.content.Context
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lifelog.app.data.ActionItem
import com.lifelog.app.data.ActionParser
import com.lifelog.app.data.Api
import com.lifelog.app.data.BriefingParser
import com.lifelog.app.data.CalendarEvent
import com.lifelog.app.data.CalendarEventParser
import com.lifelog.app.data.ChatParser
import com.lifelog.app.data.ChatRequest
import com.lifelog.app.data.DailyBriefing
import com.lifelog.app.data.GmailMessage
import com.lifelog.app.data.GmailParser
import com.lifelog.app.data.GoogleStatus
import com.lifelog.app.data.GoogleStatusParser
import com.lifelog.app.data.Memory
import com.lifelog.app.data.MemoryParser
import com.lifelog.app.data.SearchParser
import com.lifelog.app.data.SearchResult
import com.lifelog.app.data.ServerStatus
import com.lifelog.app.data.StatusParser
import com.lifelog.app.data.UploadResponse
import com.lifelog.app.data.UploadParser
import com.lifelog.app.data.userMessage
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import java.io.File

data class ChatMessage(val role: String, val content: String)

data class AppState(
    val loading: Boolean = false,
    val uploading: Boolean = false,
    val memories: List<Memory> = emptyList(),
    val lastUpload: UploadResponse? = null,
    val googleStatus: GoogleStatus? = null,
    val upcomingEvents: List<CalendarEvent> = emptyList(),
    val importantEmails: List<GmailMessage> = emptyList(),
    val actions: List<ActionItem> = emptyList(),
    val briefing: DailyBriefing? = null,
    val briefingLoading: Boolean = false,
    val serverStatus: ServerStatus? = null,
    val chatMessages: List<ChatMessage> = emptyList(),
    val chatLoading: Boolean = false,
    val chatSources: List<SearchResult> = emptyList(),
)

class LifeLogViewModel : ViewModel() {
    private val _state = MutableStateFlow(AppState())
    val state: StateFlow<AppState> = _state
    private val _searchResults = MutableStateFlow<List<SearchResult>>(emptyList())
    val searchResults: StateFlow<List<SearchResult>> = _searchResults

    fun loadMemories() = viewModelScope.launch {
        _state.value = _state.value.copy(loading = true)
        runCatching { Api.service.memories() }
            .onSuccess { _state.value = _state.value.copy(loading = false, memories = MemoryParser.parse(it)) }
            .onFailure { _state.value = _state.value.copy(loading = false) }
    }

    fun delete(id: String, onError: (String) -> Unit) = viewModelScope.launch {
        runCatching { Api.service.delete(id) }
            .onSuccess { _state.value = _state.value.copy(memories = _state.value.memories.filterNot { it.id == id }) }
            .onFailure { onError(it.userMessage()) }
    }

    fun search(query: String) = viewModelScope.launch {
        if (query.isBlank()) { _searchResults.value = emptyList(); return@launch }
        runCatching { Api.service.search(query) }
            .onSuccess { _searchResults.value = SearchParser.parse(it) }
            .onFailure { _searchResults.value = emptyList() }
    }

    fun upload(context: Context, uri: Uri, onDone: () -> Unit, onError: (String) -> Unit) = viewModelScope.launch {
        _state.value = _state.value.copy(uploading = true, lastUpload = null)
        runCatching {
            val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                ?: error("The selected audio file could not be read.")
            Api.uploadBytes("recording.m4a", bytes, context.contentResolver.getType(uri) ?: "audio/mp4")
        }.handleUpload(onDone, onError)
    }

    fun uploadFile(file: File, mime: String, onDone: () -> Unit, onError: (String) -> Unit) = viewModelScope.launch {
        _state.value = _state.value.copy(uploading = true, lastUpload = null)
        runCatching { Api.uploadBytes(file.name, file.readBytes(), mime) }.handleUpload(onDone, onError)
    }

    fun loadGoogleStatus() = viewModelScope.launch {
        runCatching { Api.service.googleStatus() }
            .onSuccess { _state.value = _state.value.copy(googleStatus = GoogleStatusParser.parse(it)) }
    }

    fun disconnectGoogle(onDone: () -> Unit = {}, onError: (String) -> Unit = {}) = viewModelScope.launch {
        runCatching { Api.service.googleDisconnect() }
            .onSuccess {
                _state.value = _state.value.copy(
                    googleStatus = GoogleStatus(connected = false),
                    upcomingEvents = emptyList(),
                    importantEmails = emptyList(),
                )
                onDone()
            }
            .onFailure { onError(it.userMessage()) }
    }

    fun loadUpcomingEvents() = viewModelScope.launch {
        val now = java.time.Instant.now().toString()
        val later = java.time.Instant.now().plusSeconds(7 * 24 * 3600).toString()
        runCatching { Api.service.googleEvents(timeMin = now, timeMax = later) }
            .onSuccess { _state.value = _state.value.copy(upcomingEvents = CalendarEventParser.parse(it)) }
    }

    fun loadImportantEmails() = viewModelScope.launch {
        runCatching { Api.service.googleImportantMessages(10) }
            .onSuccess { _state.value = _state.value.copy(importantEmails = GmailParser.parse(it)) }
    }

    fun loadActions() = viewModelScope.launch {
        runCatching { Api.service.actions() }
            .onSuccess { _state.value = _state.value.copy(actions = ActionParser.parse(it)) }
    }

    fun loadBriefing() = viewModelScope.launch {
        _state.value = _state.value.copy(briefingLoading = true)
        runCatching { Api.service.dailyBriefing() }
            .onSuccess { _state.value = _state.value.copy(briefing = BriefingParser.parse(it), briefingLoading = false) }
            .onFailure { _state.value = _state.value.copy(briefingLoading = false) }
    }

    fun loadServerStatus() = viewModelScope.launch {
        runCatching { Api.service.status() }
            .onSuccess { _state.value = _state.value.copy(serverStatus = StatusParser.parse(it)) }
    }

    fun sendChat(question: String) = viewModelScope.launch {
        val q = question.trim()
        if (q.isEmpty() || _state.value.chatLoading) return@launch
        _state.value = _state.value.copy(
            chatMessages = _state.value.chatMessages + ChatMessage("user", q),
            chatLoading = true,
        )
        runCatching { Api.service.chat(ChatRequest(q)) }
            .onSuccess { element ->
                val response = ChatParser.parse(element)
                _state.value = _state.value.copy(
                    chatMessages = _state.value.chatMessages + ChatMessage(
                        "assistant",
                        response.answer.ifBlank { "I couldn't find an answer in your memories." },
                    ),
                    chatSources = response.sources,
                    chatLoading = false,
                )
            }
            .onFailure { error ->
                _state.value = _state.value.copy(
                    chatMessages = _state.value.chatMessages + ChatMessage("assistant", error.userMessage()),
                    chatLoading = false,
                )
            }
    }

    fun clearChat() {
        _state.value = _state.value.copy(chatMessages = emptyList(), chatSources = emptyList())
    }

    private fun Result<UploadResponse>.handleUpload(onDone: () -> Unit, onError: (String) -> Unit) {
        onSuccess {
            if (!it.success) onError(it.error ?: it.detail ?: "The server could not process this audio.")
            else { _state.value = _state.value.copy(uploading = false, lastUpload = it); onDone() }
        }.onFailure { _state.value = _state.value.copy(uploading = false); onError(it.userMessage()) }
    }
}
