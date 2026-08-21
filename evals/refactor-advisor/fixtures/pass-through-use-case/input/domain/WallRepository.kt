package com.example.domain

interface WallRepository {
    suspend fun byGym(gymId: GymId): List<Wall>
    suspend fun byId(wallId: WallId): Wall?
    suspend fun search(term: String): List<Wall>
}
