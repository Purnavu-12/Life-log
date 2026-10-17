package com.lifelog.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.navigation.compose.rememberNavController
import com.lifelog.app.data.Api
import com.lifelog.app.ui.LifeLogApp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Api.init(applicationContext)
        setContent { LifeLogTheme { LifeLogApp(rememberNavController()) } }
    }
}

@Composable
private fun LifeLogTheme(content: @Composable () -> Unit) {
    val dark = isSystemInDarkTheme()
    val colors = if (dark) darkColorScheme(
        primary = Color(0xFFB8A6FF),
        onPrimary = Color(0xFF231A4A),
        secondary = Color(0xFF9AD7D1),
        tertiary = Color(0xFFFFB4A2),
        background = Color(0xFF0B0B12),
        surface = Color(0xFF15151F),
        surfaceVariant = Color(0xFF232332),
    ) else lightColorScheme(
        primary = Color(0xFF5C48B5),
        onPrimary = Color.White,
        secondary = Color(0xFF176A66),
        tertiary = Color(0xFFB85C38),
        background = Color(0xFFF6F5FB),
        surface = Color.White,
        surfaceVariant = Color(0xFFECEAF5),
    )
    MaterialTheme(colorScheme = colors, content = content)
}