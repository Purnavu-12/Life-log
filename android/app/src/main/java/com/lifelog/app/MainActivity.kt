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
import com.lifelog.app.ui.LifeLogApp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { LifeLogTheme { LifeLogApp(rememberNavController()) } }
    }
}

@Composable
private fun LifeLogTheme(content: @Composable () -> Unit) {
    val dark = isSystemInDarkTheme()
    val colors = if (dark) darkColorScheme(
        primary = Color(0xFFB8A6FF),
        secondary = Color(0xFF9AD7D1),
        background = Color(0xFF0E0E13),
        surface = Color(0xFF17171F),
    ) else lightColorScheme(
        primary = Color(0xFF5C48B5),
        secondary = Color(0xFF176A66),
        background = Color(0xFFF8F7FC),
        surface = Color.White,
    )
    MaterialTheme(colorScheme = colors, content = content)
}
