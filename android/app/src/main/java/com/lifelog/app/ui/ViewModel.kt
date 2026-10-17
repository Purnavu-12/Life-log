package com.lifelog.app.ui

import android.content.Context
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lifelog.app.data.Api
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

    private fun Result<UploadResponse>.handleUpload(onDone: () -> Unit, onError: (String) -> Unit) {
        onSuccess {
            if (!it.success) onError(it.error ?: it.detail ?: "The server could not process this audio.")
            else { _state.value = _state.value.copy(uploading = false, lastUpload = it); onDone() }
        }.onFailure { _state.value = _state.value.copy(uploading = false); onError(it.userMessage()) }
    }
}
