package com.lifelog.app.data

import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener

object EventSocket {
    private val client = OkHttpClient()
    private var socket: WebSocket? = null

    private val _connected = MutableStateFlow(false)
    val connected: StateFlow<Boolean> = _connected.asStateFlow()

    private val _events = MutableStateFlow<List<LiveEvent>>(emptyList())
    val events: StateFlow<List<LiveEvent>> = _events.asStateFlow()

    fun connect(baseUrl: String) {
        disconnect()
        val wsUrl = toEventsUrl(baseUrl)
        Log.d("LifeLogWS", "Connecting to $wsUrl")
        val request = Request.Builder().url(wsUrl).build()
        socket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.d("LifeLogWS", "Connected to $wsUrl")
                _connected.value = true
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                Log.d("LifeLogWS", "Received: $text")
                val event = EventParser.parse(text)
                _events.value = listOf(event) + _events.value.take(99)
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                _connected.value = false
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e("LifeLogWS", "Failure: ${t.message}", t)
                _connected.value = false
            }
        })
    }

    fun disconnect() {
        socket?.close(1000, "bye")
        socket = null
        _connected.value = false
    }

    fun clear() {
        _events.value = emptyList()
    }

    private fun toEventsUrl(baseUrl: String): String {
        val trimmed = baseUrl.trim().trimEnd('/')
        val wsBase = when {
            trimmed.startsWith("https://", ignoreCase = true) -> "wss://" + trimmed.removePrefix("https://")
            trimmed.startsWith("http://", ignoreCase = true) -> "ws://" + trimmed.removePrefix("http://")
            trimmed.startsWith("wss://", ignoreCase = true) -> trimmed
            trimmed.startsWith("ws://", ignoreCase = true) -> trimmed
            else -> "ws://$trimmed"
        }
        return "$wsBase/events"
    }
}