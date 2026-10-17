package com.lifelog.app.data

import com.lifelog.app.BuildConfig
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
import retrofit2.http.Query
import retrofit2.http.Path
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
}

object Api {
    private val json = Json { ignoreUnknownKeys = true }
    private val client = OkHttpClient.Builder().build()
    val service: LifeLogService = Retrofit.Builder()
        .baseUrl(BuildConfig.API_BASE_URL)
        .client(client)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()
        .create(LifeLogService::class.java)

    suspend fun uploadBytes(name: String, bytes: ByteArray, mime: String): UploadResponse {
        val body = bytes.toRequestBody(mime.toMediaType())
        return service.upload(MultipartBody.Part.createFormData("file", name, body))
    }
}

fun Throwable.userMessage(): String = when (this) {
    is IOException -> "Could not reach LifeLog. Check that the server is running."
    else -> message?.takeIf { it.isNotBlank() } ?: "Something went wrong. Please try again."
}
