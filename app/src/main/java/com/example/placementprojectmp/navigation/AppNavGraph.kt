package com.example.placementprojectmp.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import androidx.navigation.compose.rememberNavController
import com.example.placementprojectmp.ui.screens.AboutAppScreen
import com.example.placementprojectmp.ui.screens.LoadingScreen
import com.example.placementprojectmp.ui.screens.LoginScreen
import com.example.placementprojectmp.ui.screens.RoleSelectionScreen
import com.example.placementprojectmp.ui.screens.SplashScreen

@Composable
fun AppNavGraph(
    navController: NavHostController = rememberNavController(),
    modifier: androidx.compose.ui.Modifier = androidx.compose.ui.Modifier
) {
    NavHost(
        navController = navController,
        startDestination = Routes.Splash,
        modifier = modifier
    ) {
        composable(Routes.Splash) {
            var hasNavigated by remember { mutableStateOf(false) }
            SplashScreen(
                modifier = modifier,
                onNavigateToAbout = {
                    if (!hasNavigated) {
                        hasNavigated = true
                        navController.navigate(Routes.About) {
                            popUpTo(Routes.Splash) { inclusive = true }
                        }
                    }
                }
            )
        }

        composable(Routes.About) {
            AboutAppScreen(
                modifier = modifier,
                onNavigateToRoleSelection = {
                    navController.navigate(Routes.RoleSelection) {
                        launchSingleTop = true
                    }
                }
            )
        }

        composable(Routes.RoleSelection) {
            RoleSelectionScreen(
                modifier = modifier,
                onNavigateToLogin = { role ->
                    navController.navigate("login?role=$role") {
                        launchSingleTop = true
                    }
                }
            )
        }

        composable(Routes.Login) {
            LoginScreen(
                modifier = modifier,
                selectedRole = "user",
                onNavigateToLoading = {
                    navController.navigate(Routes.Loading) {
                        launchSingleTop = true
                    }
                }
            )
        }

        composable(
            route = Routes.LoginWithRole,
            arguments = listOf(
                navArgument("role") { type = NavType.StringType; defaultValue = "user" }
            )
        ) { backStackEntry ->
            val role = backStackEntry.arguments?.getString("role") ?: "user"
            LoginScreen(
                modifier = modifier,
                selectedRole = role,
                onNavigateToLoading = {
                    navController.navigate(Routes.Loading) {
                        launchSingleTop = true
                    }
                }
            )
        }

        composable(Routes.Loading) {
            var hasNavigated by remember { mutableStateOf(false) }
            LoadingScreen(
                modifier = modifier,
                isSignUp = false,
                onNavigateToAbout = {
                    if (!hasNavigated) {
                        hasNavigated = true
                        navController.navigate(Routes.About) {
                            popUpTo(Routes.About) { inclusive = true }
                        }
                    }
                }
            )
        }
    }
}
