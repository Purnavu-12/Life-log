package com.lifelog.app.ui

import android.content.Context
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lifelog.app.data.Api
import com.lifelog.app.data.CalendarsResponse
import com.lifelog.app.data.GoogleEvent
import com.lifelog.app.data.GoogleEventsResponse
import com.lifelog.app.data.GoogleMessagesResponse
import com.lifelog.app.data.GoogleProfileResponse
import com.lifelog.app.data.GoogleState
import com.lifelog.app.data.GoogleStatus
import com.lifelog.app.data.GmailMessage
import com.lifelog.app.data.Memory
import com.lifelog.app.data.SearchResult
import com.lifelog.app.data.UploadResponse
import com.lifelog.app.data.userMessage
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import java.io.File

data class AppState(
    val loading: Boolean = false,
    val uploading: Boolean = false,
    val memories: List<Memory> = emptyList(),
    val lastUpload: UploadResponse? = null,
    val googleStatus: GoogleStatus? = null,
    val upcomingEvents: List<GoogleEvent> = emptyList(),
    val importantEmails: List<GmailMessage> = emptyList(),
)

class LifeLogViewModel : ViewModel() {
    private val _state = MutableStateFlow(AppState())
    val state: StateFlow<AppState> = _state
    private val _searchResults = MutableStateFlow<List<SearchResult>>(emptyList())
    val searchResults: StateFlow<List<SearchResult>> = _searchResults

    fun loadMemories() = viewModelScope.launch {
        _state.value = _state.value.copy(loading = true)
        runCatching { Api.service.memories() }
            .onSuccess { _state.value = _state.value.copy(loading = false, memories = it.memories) }
            .onFailure { _state.value = _state.value.copy(loading = false) }
    }

    fun delete(id: String, onError: (String) -> Unit) = viewModelScope.launch {
        runCatching { Api.service.delete(id) }
            .onSuccess { _state.value = _state.value.copy(memories = _state.value.memories.filterNot { it.id == id }) }
            .onFailure { onError(it.userMessage()) }
    }

    fun search(query: String) = viewModelScope.launch {
        if (query.isBlank()) { _searchResults.value = emptyList(); return@launch }
        runCatching { Api.service.search(query) }.onSuccess { _searchResults.value = it.results }
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
            .onSuccess { _state.value = _state.value.copy(googleStatus = it) }
    }

    fun disconnectGoogle(onDone: () -> Unit = {}, onError: (String) -> Unit = {}) = viewModelScope.launch {
        runCatching { Api.service.googleDisconnect() }
            .onSuccess {
                _state.value = _state.value.copy(googleStatus = GoogleStatus(connected = false), upcomingEvents = emptyList(), importantEmails = emptyList())
                onDone()
            }
            .onFailure { onError(it.userMessage()) }
    }

    fun loadUpcomingEvents() = viewModelScope.launch {
        if (_state.value.googleStatus?.connected != true) return@launch
        val now = java.time.Instant.now().toString()
        val later = java.time.Instant.now().plusSeconds(7 * 24 * 3600).toString()
        runCatching { Api.service.googleEvents(timeMin = now, timeMax = later) }
            .onSuccess { _state.value = _state.value.copy(upcomingEvents = it.events) }
    }

    fun loadImportantEmails() = viewModelScope.launch {
        if (_state.value.googleStatus?.connected != true) return@launch
        runCatching { Api.service.googleImportantMessages(10) }
            .onSuccess { _state.value = _state.value.copy(importantEmails = it.messages) }
    }

    private fun Result<UploadResponse>.handleUpload(onDone: () -> Unit, onError: (String) -> Unit) {
        onSuccess {
            if (!it.success) onError(it.error ?: it.detail ?: "The server could not process this audio.")
            else { _state.value = _state.value.copy(uploading = false, lastUpload = it); onDone() }
        }.onFailure { _state.value = _state.value.copy(uploading = false); onError(it.userMessage()) }
    }
}
