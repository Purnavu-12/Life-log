package com.lifelog.app.data

import android.content.Context
import android.content.SharedPreferences
import com.lifelog.app.BuildConfig
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path
import retrofit2.http.Query
import java.io.IOException

interface LifeLogService {
    @Multipart
    @POST("api/upload")
    suspend fun upload(@Part file: MultipartBody.Part): UploadResponse

    @GET("api/memories")
    suspend fun memories(@Query("limit") limit: Int = 50, @Query("offset") offset: Int = 0): MemoriesResponse

    @DELETE("api/memories/{id}")
    suspend fun delete(@Path("id") id: String)

    @POST("api/search")
    suspend fun search(@Query("query") query: String, @Query("threshold") threshold: Double = 0.5): SearchResponse

    @GET("auth/google/status")
    suspend fun googleStatus(): GoogleStatus

    @POST("auth/google/disconnect")
    suspend fun googleDisconnect(): SimpleResponse

    @GET("api/google/calendars")
    suspend fun googleCalendars(): CalendarsResponse

    @GET("api/google/events")
    suspend fun googleEvents(
        @Query("calendar_id") calendarId: String = "primary",
        @Query("time_min") timeMin: String? = null,
        @Query("time_max") timeMax: String? = null,
    ): GoogleEventsResponse

    @GET("api/google/messages/important")
    suspend fun googleImportantMessages(@Query("max_results") maxResults: Int = 10): GoogleMessagesResponse

    @GET("api/google/profile")
    suspend fun googleProfile(): GoogleProfileResponse
}

object Api {
    private const val PREFS_NAME = "lifelog_settings"
    private const val KEY_SERVER_URL = "server_url"

    private val json = Json { ignoreUnknownKeys = true }
    private lateinit var prefs: SharedPreferences

    private val _baseUrl = MutableStateFlow(normalize(BuildConfig.API_BASE_URL))
    val baseUrlFlow: StateFlow<String> = _baseUrl.asStateFlow()

    fun init(context: Context) {
        prefs = context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val stored = prefs.getString(KEY_SERVER_URL, null)
        if (!stored.isNullOrBlank()) {
            _baseUrl.value = normalize(stored)
        }
    }

    fun setBaseUrl(url: String) {
        val normalized = normalize(url)
        if (::prefs.isInitialized) {
            prefs.edit().putString(KEY_SERVER_URL, normalized).apply()
        }
        _baseUrl.value = normalized
    }

    val service: LifeLogService
        get() {
            val url = _baseUrl.value
            if (url != cachedUrl || cachedService == null) {
                cachedUrl = url
                val client = OkHttpClient.Builder().build()
                cachedService = Retrofit.Builder()
                    .baseUrl(url)
                    .client(client)
                    .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
                    .build()
                    .create(LifeLogService::class.java)
            }
            return cachedService!!
        }

    suspend fun uploadBytes(name: String, bytes: ByteArray, mime: String): UploadResponse {
        val body = bytes.toRequestBody(mime.toMediaType())
        return service.upload(MultipartBody.Part.createFormData("file", name, body))
    }

    private fun normalize(url: String): String {
        val trimmed = url.trim()
        return if (trimmed.endsWith("/")) trimmed else "$trimmed/"
    }

    private var cachedUrl: String? = null
    private var cachedService: LifeLogService? = null
}

fun Throwable.userMessage(): String = when (this) {
    is IOException -> "Could not reach LifeLog. Check the server URL and your connection."
    else -> message?.takeIf { it.isNotBlank() } ?: "Something went wrong. Please try again."
}