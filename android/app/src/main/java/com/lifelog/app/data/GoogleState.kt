package com.lifelog.app.data

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

object GoogleState {
    private val _connectedEvent = MutableStateFlow<String?>(null)
    val connectedEvent: StateFlow<String?> = _connectedEvent.asStateFlow()

    fun markConnected(email: String?) {
        _connectedEvent.value = email ?: "connected"
    }

    fun consume() {
        _connectedEvent.value = null
    }
}