package com.lifelog.app.data

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

object GoogleState {
    private val _connectedEvent = MutableStateFlow<String?>(null)
    val connectedEvent: StateFlow<String?> = _connectedEvent.asStateFlow()

    /** Incremented whenever the app returns to the foreground, so the UI can re-check OAuth state. */
    private val _refreshTrigger = MutableStateFlow(0)
    val refreshTrigger: StateFlow<Int> = _refreshTrigger.asStateFlow()

    fun markConnected(email: String?) {
        _connectedEvent.value = email ?: "connected"
    }

    fun triggerRefresh() {
        _refreshTrigger.value = _refreshTrigger.value + 1
    }

    fun consume() {
        _connectedEvent.value = null
    }
}
