package com.example.placementprojectmp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import com.example.placementprojectmp.ui.screens.AboutAppScreen
import com.example.placementprojectmp.ui.screens.LoadingScreen
import com.example.placementprojectmp.ui.screens.LoginScreen
import com.example.placementprojectmp.ui.screens.SplashScreen
import com.example.placementprojectmp.ui.theme.PlacementProjectMPTheme
import kotlinx.coroutines.delay

enum class AppScreen { Splash, Login, Loading, About }

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            PlacementProjectMPTheme {
                AppContent(modifier = Modifier.fillMaxSize())
            }
        }
    }
}

@Composable
private fun AppContent(modifier: Modifier = Modifier) {
    var currentScreen by remember { mutableStateOf(AppScreen.Splash) }
    var isSignUp by remember { mutableStateOf(false) }

    when (currentScreen) {
        AppScreen.Splash -> {
            SplashScreen(modifier = modifier)
            LaunchedEffect(Unit) {
                delay(2200)
                currentScreen = AppScreen.Login
            }
        }
        AppScreen.Login -> LoginScreen(
            isSignUp = isSignUp,
            onToggleSignUp = { isSignUp = !isSignUp },
            onLogin = { signUp ->
                isSignUp = signUp
                currentScreen = AppScreen.Loading
            },
            modifier = modifier
        )
        AppScreen.Loading -> {
            LoadingScreen(isSignUp = isSignUp, modifier = modifier)
            LaunchedEffect(Unit) {
                delay(2500)
                currentScreen = AppScreen.About
            }
        }
        AppScreen.About -> AboutAppScreen(modifier = modifier)
    }
}
