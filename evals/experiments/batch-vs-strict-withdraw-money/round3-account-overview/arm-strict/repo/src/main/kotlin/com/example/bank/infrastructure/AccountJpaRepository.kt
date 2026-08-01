package com.example.bank.infrastructure

import org.springframework.data.jpa.repository.JpaRepository

interface AccountJpaRepository : JpaRepository<AccountJpaEntity, String>
