package com.example.bank.infrastructure.persistence

import org.springframework.data.jpa.repository.JpaRepository

/** Persistence primitive used only by [AccountRepositoryAdapter]. */
interface AccountJpaRepository : JpaRepository<AccountJpaEntity, String>
