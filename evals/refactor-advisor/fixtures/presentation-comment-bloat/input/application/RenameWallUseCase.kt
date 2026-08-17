package com.example.application

class RenameWallUseCase(
    private val walls: WallRepository,
) {
    suspend operator fun invoke(wallId: WallId, name: String) {
        val wall = walls.byId(wallId) ?: throw WallNotFound(wallId)
        walls.save(wall.renamedTo(name))
    }
}
