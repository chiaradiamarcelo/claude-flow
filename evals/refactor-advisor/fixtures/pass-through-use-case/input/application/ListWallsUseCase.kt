package com.example.application

class ListWallsUseCase(
    private val walls: WallRepository,
) {
    suspend operator fun invoke(gymId: GymId): List<Wall> = walls.byGym(gymId)
}
