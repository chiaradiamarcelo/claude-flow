package com.example.bank.infrastructure

import org.springframework.data.jpa.repository.JpaRepository

internal interface AccountJpaRepository : JpaRepository<AccountJpaEntity, String>
